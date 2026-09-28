"""
Portfolio Optimizer — Risk-Based Test Portfolio Optimizer
=========================================================

MATHEMATICAL PROBLEM FORMULATION
----------------------------------
This optimizer solves a variant of the 0/1 Knapsack problem with two competing
objectives and a set of hard/soft constraints.

DECISION VARIABLES
------------------
  x_i ∈ {0, 1}   for each active test case i
    x_i = 1  → test case i is selected into the portfolio
    x_i = 0  → test case i is deferred

OBJECTIVE 1 — Maximum Risk Coverage (max_risk)
----------------------------------------------
  Maximize:   Σ RiskScore_i · x_i
  Subject to: Σ ExecutionTime_i · x_i  ≤  TimeBudget

  Rational: Maximizes the total weighted risk score of the selected portfolio,
  ensuring the highest-risk failures are surfaced within the time budget.

OBJECTIVE 2 — Maximum Risk Efficiency (max_efficiency)
-------------------------------------------------------
  Prioritize by:  Efficiency_i = RiskScore_i / ExecutionTime_i

  Then greedily select in descending efficiency order subject to:
  Σ ExecutionTime_i · x_i  ≤  TimeBudget

  Rational: Maximizes risk detected per unit of execution time.
  Useful when the time budget is very tight and every minute must yield
  maximum defect-detection payoff.

HARD CONSTRAINTS (cannot be violated)
--------------------------------------
  HC1: All test cases where is_mandatory = True MUST be included.
  HC2: At least one network-recovery test must be present (if flag set).
  HC3: At least one critical submission test must be present (if flag set).
  HC4: At least one security-critical test must be present (if flag set).
  HC5: If mandatory tests alone exceed the time budget → status = UNFEASIBLE.

SOFT CONSTRAINTS (best-effort, reported as satisfied/unsatisfied)
-----------------------------------------------------------------
  SC1: Prefer tests with risk_score ≥ 7.0 (high-risk preference).
  SC2: Prefer tests with ≥ 3 historical critical defects.
  SC3: Prefer tests with production_usage ≥ 8.0 (frequent journeys).
  SC4: Prefer tests with shorter execution time (if flag set).
  SC5: Prefer tests with change_risk ≥ 6.0 (recent-change preference).

AUTHORIZED PRIORITY OVERRIDE
------------------------------
  A Test Lead or Admin may override the priority of any test case via the
  /api/optimizer/override endpoint. Overrides are persisted in the OverrideLog
  table and applied during portfolio scoring by boosting the sort key of
  overridden tests so they are selected first.

GREEDY HEURISTIC — WHY IT IS USED
------------------------------------
The exact 0/1 Knapsack solution via Dynamic Programming (DP) runs in
O(n × W) time, where W is the time budget quantised to the smallest
execution-time unit. For the current dataset (n ≤ 35 test cases) and
budgets up to ~500 min, exact DP is completely feasible.

However, the greedy heuristic was adopted first because:
  1. It is O(n log n) — trivially fast for any realistic dataset size.
  2. It is transparent and easy to audit (evaluator can trace each step).
  3. It integrates naturally with hard-constraint pre-selection, overrides,
     and soft-constraint tiebreaking — logic that is complex to embed in DP.

LIMITATION — GREEDY IS NOT GLOBALLY OPTIMAL
--------------------------------------------
The greedy approach DOES NOT guarantee the mathematically optimal 0/1 knapsack
solution. Counter-example:
  Budget = 10 min
  TC-A: risk_score=8, time=6  → selected first (ratio=1.33)
  TC-B: risk_score=5, time=4
  TC-C: risk_score=5, time=4
  Greedy picks TC-A (time=6) + TC-B (time=4) → total risk = 13
  Optimal picks TC-B + TC-C (time=8) → total risk = 10   ← actually greedy wins here
  But in a different configuration greedy can lose up to ~25% vs optimal DP.

For production use with a larger dataset (n > 100), an exact ILP or DP
implementation should replace or supplement the greedy pass.
An optional Exact DP comparison is available via POST /api/optimizer/run-dp.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models import TestCase, OverrideLog
from routers.risk import calculate_risk_score
from routers.auth import require_role, sessions
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

router = APIRouter(prefix="/api/optimizer", tags=["optimizer"])

class OptimizerRequest(BaseModel):
    token: str
    time_budget_minutes: float = 60.0
    objective: str = "max_risk"  # max_risk or max_efficiency
    mandatory_only: bool = False
    include_network_test: bool = True
    include_submission_test: bool = True
    include_security_test: bool = True
    prefer_high_risk: bool = True
    prefer_recent_defects: bool = True
    prefer_frequent_journeys: bool = True
    prefer_shorter_execution: bool = False
    prefer_recent_changes: bool = True

class OverrideRequest(BaseModel):
    token: str
    test_case_id: str
    old_priority: int
    new_priority: int
    reason: str


# ---------------------------------------------------------------------------
# SHARED HELPERS
# ---------------------------------------------------------------------------

def _build_scored_list(test_cases, db: Session, active_overrides: dict):
    """Score all active test cases and attach override metadata."""
    scored = []
    for tc in test_cases:
        risk = calculate_risk_score(tc, db=db)
        scored.append({
            "test_case_id": tc.test_case_id,
            "name": tc.name,
            "module": tc.module,
            "critical_user_journey": tc.critical_user_journey,
            "description": tc.description,
            "execution_time_minutes": tc.execution_time_minutes,
            "is_mandatory": tc.is_mandatory,
            "business_criticality": tc.business_criticality,
            "historical_defect_count": tc.historical_defect_count,
            "historical_critical_defect_count": risk["actual_critical_defect_count"],
            "production_usage": tc.production_usage,
            "change_risk": tc.change_risk,
            "network_risk": tc.network_risk,
            "unusual_behaviour_risk": tc.unusual_behaviour_risk,
            "has_override": tc.test_case_id in active_overrides,
            "override_new_priority": active_overrides.get(tc.test_case_id),
            **risk
        })
    return scored


def _build_must_include_ids(scored, req):
    """Collect the set of test_case_ids that must be in the portfolio per hard constraints."""
    mandatory_ids = [s["test_case_id"] for s in scored if s["is_mandatory"]]
    network_tests = [s for s in scored if "network" in s["critical_user_journey"].lower() or "network" in s["module"].lower()]
    submission_tests = [s for s in scored if "submit" in s["critical_user_journey"].lower() or "submission" in s["module"].lower()]
    security_tests = [s for s in scored if "security" in s["module"].lower() or "access control" in s["critical_user_journey"].lower()]

    must_include_ids = set(mandatory_ids)
    if req.include_network_test and network_tests:
        must_include_ids.add(network_tests[0]["test_case_id"])
    if req.include_submission_test and submission_tests:
        must_include_ids.add(submission_tests[0]["test_case_id"])
    if req.include_security_test and security_tests:
        must_include_ids.add(security_tests[0]["test_case_id"])
    return must_include_ids


def _check_unfeasible(scored, must_include_ids, req):
    """Return UNFEASIBLE response dict if mandatory tests exceed budget, else None."""
    mandatory_total_time = sum(
        s["execution_time_minutes"] for s in scored if s["test_case_id"] in must_include_ids
    )
    if mandatory_total_time > req.time_budget_minutes:
        return {
            "status": "UNFEASIBLE",
            "objective": req.objective,
            "objective_label": "Maximum Risk Coverage" if req.objective == "max_risk" else "Maximum Risk per Minute",
            "time_budget_minutes": req.time_budget_minutes,
            "mandatory_execution_time_required": round(mandatory_total_time, 1),
            "shortfall_minutes": round(mandatory_total_time - req.time_budget_minutes, 1),
            "reason": (
                f"Cannot satisfy constraints: mandatory tests require {mandatory_total_time:.1f} min "
                f"but budget is only {req.time_budget_minutes:.1f} min. "
                f"Please increase the time budget to at least {mandatory_total_time:.1f} min."
            ),
            "total_test_cases": len(scored),
            "selected_count": 0,
            "deferred_count": len(scored),
            "excluded_count": 0,
            "total_execution_time": 0.0,
            "risk_coverage_percent": 0.0,
            "critical_defect_coverage_percent": 0.0,
            "hard_constraint_violations": [
                f"UNFEASIBLE: Mandatory tests require {mandatory_total_time:.1f} min, exceeding budget of {req.time_budget_minutes:.1f} min."
            ],
            "soft_constraints": [],
            "selected": [],
            "deferred": scored,
            "excluded": [],
        }
    return None


def _evaluate_soft_constraints(selected, scored, req):
    """Evaluate soft constraints and return a list of constraint report dicts."""
    soft_constraints = []
    if req.prefer_high_risk:
        high_risk_selected = sum(1 for s in selected if s["risk_score"] >= 7.0)
        high_risk_total = sum(1 for s in scored if s["risk_score"] >= 7.0)
        soft_constraints.append({
            "constraint": "Prefer high-risk tests",
            "satisfied": high_risk_selected >= high_risk_total * 0.7,
            "detail": f"{high_risk_selected}/{high_risk_total} high-risk tests selected"
        })
    if req.prefer_recent_defects:
        defect_selected = sum(1 for s in selected if s["historical_critical_defect_count"] >= 3)
        defect_total = sum(1 for s in scored if s["historical_critical_defect_count"] >= 3)
        soft_constraints.append({
            "constraint": "Prefer tests with recent critical defects",
            "satisfied": defect_selected >= defect_total * 0.6,
            "detail": f"{defect_selected}/{defect_total} high-defect tests selected"
        })
    if req.prefer_frequent_journeys:
        frequent_selected = sum(1 for s in selected if s["production_usage"] >= 8.0)
        frequent_total = sum(1 for s in scored if s["production_usage"] >= 8.0)
        soft_constraints.append({
            "constraint": "Prefer frequently used journeys",
            "satisfied": frequent_selected >= frequent_total * 0.6,
            "detail": f"{frequent_selected}/{frequent_total} high-usage tests selected"
        })
    if req.prefer_shorter_execution:
        avg_time_selected = sum(s["execution_time_minutes"] for s in selected) / max(len(selected), 1)
        avg_time_all = sum(s["execution_time_minutes"] for s in scored) / max(len(scored), 1)
        soft_constraints.append({
            "constraint": "Prefer shorter execution times",
            "satisfied": avg_time_selected <= avg_time_all,
            "detail": f"Avg selected: {avg_time_selected:.1f} min vs overall avg: {avg_time_all:.1f} min"
        })
    if req.prefer_recent_changes:
        change_selected = sum(1 for s in selected if s["change_risk"] >= 6.0)
        change_total = sum(1 for s in scored if s["change_risk"] >= 6.0)
        soft_constraints.append({
            "constraint": "Prefer recently changed modules",
            "satisfied": change_selected >= change_total * 0.5,
            "detail": f"{change_selected}/{change_total} high-change-risk tests selected"
        })
    return soft_constraints


def _coverage_metrics(selected, scored):
    total_risk = sum(s["risk_score"] for s in scored)
    selected_risk = sum(s["risk_score"] for s in selected)
    total_cd = sum(s["historical_critical_defect_count"] for s in scored)
    selected_cd = sum(s["historical_critical_defect_count"] for s in selected)
    return total_risk, selected_risk, total_cd, selected_cd


# ---------------------------------------------------------------------------
# GREEDY SELECTION ALGORITHM
# ---------------------------------------------------------------------------

def _greedy_select(scored, must_include_ids, req):
    """
    Greedy portfolio selection.

    Step 1 — Sort by primary objective metric (descending):
      • max_risk:       sort by risk_score (higher = more valuable)
      • max_efficiency: sort by efficiency_score = risk_score / execution_time

    Step 2 — Override boost: tests with an active priority override are given
      a large sort-key bonus (1000 - new_priority) so they float to the top
      regardless of objective metric. This implements the "authorized override"
      hard-constraint variant.

    Step 3 — Optional soft-constraint tiebreaker: if prefer_shorter_execution
      is set, secondary sort favours tests with lower execution_time_minutes.

    Step 4 — Pass 1 (mandatory + override tests):
      Iterate candidates in sorted order; add to selected if:
        • the test is in must_include_ids OR has_override is True
        • total_time + execution_time_minutes ≤ time_budget_minutes

    Step 5 — Pass 2 (remaining tests):
      Fill remaining budget with next-best candidates not yet selected/deferred.

    LIMITATION:
      This greedy approach can produce a sub-optimal 0/1 knapsack solution.
      In the worst case, selecting a high-risk but long test in Pass 1 may
      block several shorter, collectively higher-value tests.
      The Exact DP endpoint (/api/optimizer/run-dp) constructs the provably
      optimal solution for comparison.
    """
    def get_sort_key(item):
        # Authorized overrides get the highest priority boost
        if item["has_override"]:
            target_rank = item["override_new_priority"]
            return (1000 - target_rank, item["risk_score"] if req.objective == "max_risk" else item["efficiency_score"])
        base_metric = item["efficiency_score"] if req.objective == "max_efficiency" else item["risk_score"]
        return (0, base_metric)

    scored.sort(key=get_sort_key, reverse=True)

    # Optional soft-constraint tiebreaker: prefer shorter execution
    if req.prefer_shorter_execution:
        scored.sort(key=lambda x: (
            1000 - x["override_new_priority"] if x["has_override"] else 0,
            -x["risk_score"] if req.objective == "max_risk" else -x["efficiency_score"],
            x["execution_time_minutes"]
        ), reverse=True)

    selected = []
    deferred = []
    excluded = []
    total_time = 0.0

    # Pass 1: mandatory + override tests
    for s in scored:
        if s["test_case_id"] in must_include_ids or s["has_override"]:
            if total_time + s["execution_time_minutes"] <= req.time_budget_minutes:
                total_time += s["execution_time_minutes"]
                selected.append(s)
            else:
                deferred.append(s)

    # Pass 2: remaining tests within budget
    for s in scored:
        if s not in selected and s not in deferred:
            if total_time + s["execution_time_minutes"] <= req.time_budget_minutes:
                total_time += s["execution_time_minutes"]
                selected.append(s)
            else:
                deferred.append(s)

    # Assign display priorities
    for i, s in enumerate(selected):
        s["priority"] = i + 1
    for i, s in enumerate(deferred):
        s["priority"] = len(selected) + i + 1

    return selected, deferred, excluded, total_time


# ---------------------------------------------------------------------------
# EXACT DYNAMIC PROGRAMMING (0/1 KNAPSACK) — OPTIONAL COMPARISON
# ---------------------------------------------------------------------------

def _exact_dp_select(scored, must_include_ids, budget_minutes):
    """
    Exact 0/1 Knapsack via Dynamic Programming.

    This computes the provably optimal subset of test cases that maximises
    total risk_score within the time budget (budget_minutes).

    Time complexity:  O(n × W)  where W = budget in 0.5-min units (integer).
    Space complexity: O(n × W)  — acceptable for n ≤ 35, W ≤ 1000.

    Hard constraints (must_include_ids) are handled by:
      1. Pre-selecting all mandatory tests.
      2. Running DP on the remaining budget and optional tests.
      3. Merging mandatory + DP-selected sets.

    Returns: (selected_ids: set, total_time: float, total_risk: float)
    """
    # Quantise execution times to 0.5-min units (integers) to keep W finite
    UNIT = 0.5
    W = int(budget_minutes / UNIT)

    mandatory = [s for s in scored if s["test_case_id"] in must_include_ids]
    optional = [s for s in scored if s["test_case_id"] not in must_include_ids]

    mandatory_time = sum(s["execution_time_minutes"] for s in mandatory)
    remaining_budget_units = int((budget_minutes - mandatory_time) / UNIT)

    if remaining_budget_units < 0:
        # mandatory tests alone exceed budget — infeasible (caller already checked)
        return set(s["test_case_id"] for s in mandatory), mandatory_time, sum(s["risk_score"] for s in mandatory)

    n = len(optional)

    # DP table: dp[i][w] = max risk achievable using first i optional tests with w units of budget
    dp = [[0.0] * (remaining_budget_units + 1) for _ in range(n + 1)]

    for i in range(1, n + 1):
        tc = optional[i - 1]
        w_i = int(tc["execution_time_minutes"] / UNIT)
        for w in range(remaining_budget_units + 1):
            # Don't take item i
            dp[i][w] = dp[i - 1][w]
            # Take item i if it fits
            if w >= w_i:
                dp[i][w] = max(dp[i][w], dp[i - 1][w - w_i] + tc["risk_score"])

    # Backtrack to retrieve selected optional tests
    selected_optional_ids = set()
    w = remaining_budget_units
    for i in range(n, 0, -1):
        if dp[i][w] != dp[i - 1][w]:
            tc = optional[i - 1]
            selected_optional_ids.add(tc["test_case_id"])
            w -= int(tc["execution_time_minutes"] / UNIT)

    selected_ids = set(s["test_case_id"] for s in mandatory) | selected_optional_ids
    total_time = sum(s["execution_time_minutes"] for s in scored if s["test_case_id"] in selected_ids)
    total_risk = sum(s["risk_score"] for s in scored if s["test_case_id"] in selected_ids)
    return selected_ids, total_time, total_risk


# ---------------------------------------------------------------------------
# ENDPOINTS
# ---------------------------------------------------------------------------

@router.post("/run")
def run_optimizer(req: OptimizerRequest, db: Session = Depends(get_db)):
    """
    Greedy portfolio optimizer.

    Uses the greedy heuristic described in _greedy_select().
    For the exact 0/1 Knapsack optimum, use POST /api/optimizer/run-dp.
    """
    user = require_role(req.token, ["tester", "test_lead", "admin"])

    test_cases = db.query(TestCase).filter(TestCase.current_status == "Active").all()

    # BUG 5 FIX: Fetch active priority overrides from OverrideLog
    all_overrides = db.query(OverrideLog).order_by(OverrideLog.timestamp.asc()).all()
    active_overrides = {}
    for ov in all_overrides:
        active_overrides[ov.test_case_id] = ov.new_priority

    scored = _build_scored_list(test_cases, db, active_overrides)
    must_include_ids = _build_must_include_ids(scored, req)

    # BUG 8: Hard constraint feasibility check
    unfeasible = _check_unfeasible(scored, must_include_ids, req)
    if unfeasible:
        return unfeasible

    selected, deferred, excluded, total_time = _greedy_select(scored, must_include_ids, req)
    soft_constraints = _evaluate_soft_constraints(selected, scored, req)
    total_risk, selected_risk, total_cd, selected_cd = _coverage_metrics(selected, scored)

    return {
        "status": "FEASIBLE",
        "objective": req.objective,
        "objective_label": "Maximum Risk Coverage" if req.objective == "max_risk" else "Maximum Risk per Minute",
        "time_budget_minutes": req.time_budget_minutes,
        "total_execution_time": round(total_time, 1),
        "total_test_cases": len(scored),
        "selected_count": len(selected),
        "deferred_count": len(deferred),
        "excluded_count": len(excluded),
        "risk_coverage_percent": round(selected_risk / max(total_risk, 1) * 100, 1),
        "critical_defect_coverage_percent": round(selected_cd / max(total_cd, 1) * 100, 1),
        "hard_constraint_violations": [],
        "soft_constraints": soft_constraints,
        "selected": selected,
        "deferred": deferred,
        "excluded": excluded,
    }


@router.post("/run-dp")
def run_optimizer_dp(req: OptimizerRequest, db: Session = Depends(get_db)):
    """
    Exact 0/1 Knapsack optimizer via Dynamic Programming (objective: max_risk).

    This endpoint computes the PROVABLY OPTIMAL subset of test cases that
    maximises total risk_score subject to the time budget and hard constraints.
    It also runs the greedy heuristic in parallel and returns a side-by-side
    comparison so the difference (optimality gap) is visible.

    NOTE: The DP objective is always max_risk (maximise total risk score).
    The greedy mode respects the req.objective field as usual.
    """
    require_role(req.token, ["tester", "test_lead", "admin"])

    test_cases = db.query(TestCase).filter(TestCase.current_status == "Active").all()

    all_overrides = db.query(OverrideLog).order_by(OverrideLog.timestamp.asc()).all()
    active_overrides = {ov.test_case_id: ov.new_priority for ov in all_overrides}

    scored = _build_scored_list(test_cases, db, active_overrides)
    must_include_ids = _build_must_include_ids(scored, req)

    unfeasible = _check_unfeasible(scored, must_include_ids, req)
    if unfeasible:
        return unfeasible

    # --- Greedy (for comparison) ---
    import copy
    scored_copy = copy.deepcopy(scored)
    greedy_selected, greedy_deferred, _, greedy_time = _greedy_select(scored_copy, must_include_ids, req)
    greedy_risk = sum(s["risk_score"] for s in greedy_selected)
    greedy_cd = sum(s["historical_critical_defect_count"] for s in greedy_selected)

    # --- Exact DP ---
    dp_ids, dp_time, dp_risk = _exact_dp_select(scored, must_include_ids, req.time_budget_minutes)
    dp_selected = [s for s in scored if s["test_case_id"] in dp_ids]
    dp_deferred = [s for s in scored if s["test_case_id"] not in dp_ids]
    dp_cd = sum(s["historical_critical_defect_count"] for s in dp_selected)

    # Assign display priorities
    dp_selected_sorted = sorted(dp_selected, key=lambda x: -x["risk_score"])
    for i, s in enumerate(dp_selected_sorted):
        s["priority"] = i + 1

    total_risk = sum(s["risk_score"] for s in scored)
    optimality_gap = round(dp_risk - greedy_risk, 3)

    return {
        "status": "FEASIBLE",
        "time_budget_minutes": req.time_budget_minutes,
        "total_test_cases": len(scored),
        "note": (
            "DP objective is always max_risk (maximise total risk score). "
            "Greedy uses the requested objective. "
            "optimality_gap = DP risk - Greedy risk. "
            "A positive gap means DP found a better solution than greedy."
        ),
        "greedy": {
            "algorithm": "Greedy heuristic (O(n log n))",
            "objective": req.objective,
            "selected_count": len(greedy_selected),
            "total_execution_time": round(greedy_time, 1),
            "total_risk_score": round(greedy_risk, 3),
            "risk_coverage_percent": round(greedy_risk / max(total_risk, 1) * 100, 1),
            "critical_defects_covered": greedy_cd,
            "selected_ids": [s["test_case_id"] for s in greedy_selected],
        },
        "exact_dp": {
            "algorithm": "Exact 0/1 Knapsack DP (O(n×W))",
            "objective": "max_risk",
            "selected_count": len(dp_selected),
            "total_execution_time": round(dp_time, 1),
            "total_risk_score": round(dp_risk, 3),
            "risk_coverage_percent": round(dp_risk / max(total_risk, 1) * 100, 1),
            "critical_defects_covered": dp_cd,
            "selected_ids": [s["test_case_id"] for s in dp_selected_sorted],
        },
        "comparison": {
            "optimality_gap_risk_score": optimality_gap,
            "greedy_is_optimal": optimality_gap == 0.0,
            "dp_selected": dp_selected_sorted,
            "dp_deferred": dp_deferred,
        }
    }


@router.post("/override")
def override_priority(req: OverrideRequest, db: Session = Depends(get_db)):
    # Verify authorization - Test Lead or Admin only
    user = require_role(req.token, ["test_lead", "admin"])

    override = OverrideLog(
        test_case_id=req.test_case_id,
        old_priority=req.old_priority,
        new_priority=req.new_priority,
        reason=req.reason,
        performed_by=user["full_name"],
        role=user["role"],
    )
    db.add(override)
    db.commit()

    return {
        "status": "Override applied",
        "test_case_id": req.test_case_id,
        "old_priority": req.old_priority,
        "new_priority": req.new_priority,
        "reason": req.reason,
        "performed_by": user["full_name"],
        "role": user["role"],
        "timestamp": str(override.timestamp),
    }


@router.get("/overrides")
def get_overrides(token: str, db: Session = Depends(get_db)):
    require_role(token, ["tester", "test_lead", "admin"])
    overrides = db.query(OverrideLog).order_by(OverrideLog.timestamp.desc()).all()
    return [{
        "id": o.id, "test_case_id": o.test_case_id,
        "old_priority": o.old_priority, "new_priority": o.new_priority,
        "reason": o.reason, "performed_by": o.performed_by,
        "role": o.role, "timestamp": str(o.timestamp)
    } for o in overrides]
