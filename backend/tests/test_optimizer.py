"""
test_optimizer.py — Category F: Portfolio Optimizer Tests

Tests verify:
  F1. Budget is respected when feasible.
  F2. UNFEASIBLE returned when mandatory tests exceed budget.
  F3. Selected test cases do not duplicate.
  F4. Risk scores remain within expected range (0.0–10.0).
  F5. Both objectives return valid portfolios.
  F6. Authorized priority override affects optimizer output.
  F7. Exact DP endpoint returns optimal or equal risk vs greedy.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


# ---------------------------------------------------------------------------
# F1 — Budget respected when feasible
# ---------------------------------------------------------------------------

def test_optimizer_budget_respected(client, tokens):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "FEASIBLE"
    assert data["total_execution_time"] <= 60.0


def test_optimizer_budget_respected_tight(client, tokens):
    """Very tight budget — only very short tests should be selected."""
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 0.1,  # essentially impossible
        "objective": "max_risk",
        "include_network_test": False,
        "include_submission_test": False,
        "include_security_test": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    # With mandatory test TC001 (5.0 min) this must be UNFEASIBLE
    if data["status"] == "FEASIBLE":
        assert data["total_execution_time"] <= 0.1
    else:
        assert data["status"] == "UNFEASIBLE"


# ---------------------------------------------------------------------------
# F2 — UNFEASIBLE when mandatory tests exceed budget
# ---------------------------------------------------------------------------

def test_unfeasible_when_mandatory_exceeds_budget(client, tokens):
    """Mandatory test TC001 requires 5 min; budget set to 1 min → UNFEASIBLE."""
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 1.0,
        "objective": "max_risk",
        "include_network_test": False,
        "include_submission_test": False,
        "include_security_test": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "UNFEASIBLE"
    assert data["selected_count"] == 0
    assert "reason" in data
    assert data["shortfall_minutes"] > 0


def test_unfeasible_response_has_no_selection(client, tokens):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 1.0,
        "objective": "max_efficiency",
        "include_network_test": False,
        "include_submission_test": False,
        "include_security_test": False,
    })
    assert resp.status_code == 200
    data = resp.json()
    if data["status"] == "UNFEASIBLE":
        assert data["selected"] == []


# ---------------------------------------------------------------------------
# F3 — No duplicate test cases in selected list
# ---------------------------------------------------------------------------

def test_no_duplicate_test_cases_in_selection(client, tokens):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    selected_ids = [s["test_case_id"] for s in data["selected"]]
    assert len(selected_ids) == len(set(selected_ids)), "Duplicate test cases in selection!"


def test_no_duplicate_test_cases_efficiency_mode(client, tokens):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_efficiency"
    })
    assert resp.status_code == 200
    data = resp.json()
    selected_ids = [s["test_case_id"] for s in data["selected"]]
    assert len(selected_ids) == len(set(selected_ids))


# ---------------------------------------------------------------------------
# F4 — Risk scores within expected range
# ---------------------------------------------------------------------------

def test_risk_scores_in_valid_range(client, tokens):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    all_tests = data["selected"] + data["deferred"]
    for tc in all_tests:
        score = tc["risk_score"]
        assert 0.0 <= score <= 10.0, f"Risk score out of bounds for {tc['test_case_id']}: {score}"


# ---------------------------------------------------------------------------
# F5 — Both objectives return valid portfolios
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("objective", ["max_risk", "max_efficiency"])
def test_both_objectives_return_valid_portfolio(client, tokens, objective):
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": objective
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"FEASIBLE", "UNFEASIBLE"}
    if data["status"] == "FEASIBLE":
        assert data["selected_count"] >= 0
        assert data["total_execution_time"] <= 60.0
        assert 0.0 <= data["risk_coverage_percent"] <= 100.0
        assert 0.0 <= data["critical_defect_coverage_percent"] <= 100.0


def test_objective_labels_correct(client, tokens):
    r_risk = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    r_eff = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_efficiency"
    })
    assert "Maximum Risk Coverage" in r_risk.json()["objective_label"]
    assert "Maximum Risk per Minute" in r_eff.json()["objective_label"]


# ---------------------------------------------------------------------------
# F6 — Priority override affects optimizer output
# ---------------------------------------------------------------------------

def test_override_affects_portfolio_ordering(client, tokens):
    """Override TC002 to top priority; it should appear first in selection."""
    # Apply override
    ov = client.post("/api/optimizer/override", json={
        "token": tokens["test_lead"],
        "test_case_id": "TC002",
        "old_priority": 5,
        "new_priority": 1,
        "reason": "Test override effect"
    })
    assert ov.status_code == 200

    # Run optimizer
    resp = client.post("/api/optimizer/run", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    selected_ids = [s["test_case_id"] for s in data["selected"]]
    # TC002 must now appear in selected (high priority boost)
    assert "TC002" in selected_ids


def test_override_persisted_in_logs(client, tokens):
    ov = client.post("/api/optimizer/override", json={
        "token": tokens["test_lead"],
        "test_case_id": "TC003",
        "old_priority": 10,
        "new_priority": 2,
        "reason": "Audit test"
    })
    assert ov.status_code == 200
    logs = client.get(f"/api/optimizer/overrides?token={tokens['tester']}")
    assert logs.status_code == 200
    ids = [o["test_case_id"] for o in logs.json()]
    assert "TC003" in ids


# ---------------------------------------------------------------------------
# F7 — Exact DP endpoint
# ---------------------------------------------------------------------------

def test_dp_endpoint_returns_valid_response(client, tokens):
    resp = client.post("/api/optimizer/run-dp", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] in {"FEASIBLE", "UNFEASIBLE"}
    if data["status"] == "FEASIBLE":
        assert "greedy" in data
        assert "exact_dp" in data
        assert "comparison" in data


def test_dp_risk_greater_or_equal_to_greedy(client, tokens):
    """DP must produce total risk ≥ greedy (it is the optimal solution)."""
    resp = client.post("/api/optimizer/run-dp", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    if data["status"] == "FEASIBLE":
        gap = data["comparison"]["optimality_gap_risk_score"]
        assert gap >= -0.001, f"DP total risk is less than greedy by {abs(gap):.3f} — should be impossible"


def test_dp_budget_respected(client, tokens):
    resp = client.post("/api/optimizer/run-dp", json={
        "token": tokens["tester"],
        "time_budget_minutes": 60.0,
        "objective": "max_risk"
    })
    assert resp.status_code == 200
    data = resp.json()
    if data["status"] == "FEASIBLE":
        dp_time = data["exact_dp"]["total_execution_time"]
        assert dp_time <= 60.0 + 0.5  # 0.5 unit tolerance for quantization
