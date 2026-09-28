# Risk-Based Test Portfolio Optimizer for an Online Examination Platform

A full-stack, transparent, and mathematically formalized **Risk-Based Test Portfolio Optimizer** built for an **Online Examination Platform** (System Under Test). Designed for college evaluation, project defense, and algorithmic benchmarking.

---

## 📐 1. Mathematical Formulation & Algorithmic Rigor

The portfolio optimizer models test suite selection as a constrained variant of the **0/1 Knapsack Problem** (Multi-Objective Integer Linear Programming / ILP formulation).

### Decision Variables
$$x_i \in \{0, 1\} \quad \forall i \in \{1, 2, \dots, n\}$$
where $x_i = 1$ if test case $i$ is selected into the test portfolio, and $x_i = 0$ if it is deferred.

### Objective Function 1: Maximum Cumulative Risk Coverage (`max_risk`)
Maximizes the total weighted risk score of the selected portfolio within the target execution time budget $B$:

$$\max \sum_{i=1}^{n} \text{RiskScore}_i \cdot x_i \quad \text{subject to} \quad \sum_{i=1}^{n} t_i \cdot x_i \le B$$

where:
- $\text{RiskScore}_i \in [0.0, 10.0]$ is the multi-factor risk score of test case $i$.
- $t_i > 0$ is the estimated execution time of test case $i$ in minutes.
- $B > 0$ is the total allocated time budget in minutes.

### Objective Function 2: Maximum Risk Efficiency (`max_efficiency`)
Maximizes the risk score detected per unit of execution time:

$$\max \sum_{i=1}^{n} e_i \cdot x_i \quad \text{where} \quad e_i = \frac{\text{RiskScore}_i}{t_i}$$

Candidates are ordered by efficiency ratio $e_i$ descending, ensuring tight time budgets achieve maximum defect-detection density per minute.

### Hard Constraints (Must be satisfied for feasibility)
- **HC1 (Mandatory Flags):** $x_i = 1 \quad \forall i \text{ where } \text{is\_mandatory}_i = \text{True}$
- **HC2 (Network Recovery Coverage):** $\sum_{i \in \text{Network}} x_i \ge 1$ (when enabled)
- **HC3 (Exam Submission Coverage):** $\sum_{i \in \text{Submission}} x_i \ge 1$ (when enabled)
- **HC4 (Security Coverage):** $\sum_{i \in \text{Security}} x_i \ge 1$ (when enabled)
- **HC5 (Time Budget Feasibility):** $\sum_{i \in \text{Mandatory}} t_i \le B$. If mandatory tests alone exceed $B$, the optimization is flagged as **`UNFEASIBLE`** and returns a shortfall report without executing invalid selections.

### Soft Constraints (Best-effort preference rules)
- **SC1 (High Risk Preference):** Prefer tests with $\text{RiskScore}_i \ge 7.0$.
- **SC2 (Historical Defect Preference):** Prefer tests with $\ge 3$ critical defects.
- **SC3 (Production Usage Preference):** Prefer tests with $\text{ProductionUsage}_i \ge 8.0$.
- **SC4 (Short Execution Preference):** Prefer tests with shorter duration $t_i$.
- **SC5 (Recent Changes Preference):** Prefer tests with $\text{ChangeRisk}_i \ge 6.0$.

### Authorized Priority Override
A **Test Lead** or **Admin** can forcibly boost candidate $k$ via `/api/optimizer/override`. Overridden candidates receive a rank bonus ($1000 - \text{new\_priority}$) that ensures top selection in Pass 1 regardless of metric, while maintaining audit logs.

### Greedy Heuristic vs. Exact 0/1 Knapsack (DP)
- **Greedy Heuristic ($O(n \log n)$):** Used by default in `POST /api/optimizer/run`. Provides fast, transparent, and auditable candidate selection.
- **Limitation:** The greedy heuristic is **not globally optimal** for 0/1 knapsack problems. When test item costs $t_i$ differ significantly, greedy ordering may lock in high-risk tests that leave unusable budget gaps.
- **Exact DP Solution ($O(n \times W)$):** Computes the provably optimal solution via 0/1 knapsack dynamic programming. Accessible via **`POST /api/optimizer/run-dp`** for side-by-side optimality gap comparison (`optimality_gap = DP_Risk - Greedy_Risk`).

---

## 🧮 2. Multi-Factor Risk Score Formula

The risk engine computes a continuous score $R_i \in [0.0, 10.0]$ using a multi-factor weighted formula:

$$R_i = 0.25 \cdot C_{\text{bus}} + 0.20 \cdot D_{\text{hist}} + 0.20 \cdot R_{\text{change}} + 0.15 \cdot U_{\text{prod}} + 0.10 \cdot R_{\text{net}} + 0.10 \cdot R_{\text{unusual}}$$

Where:
- $C_{\text{bus}}$: Business Criticality ($0-10$)
- $D_{\text{hist}}$: Historical Defect Risk, derived dynamically from actual critical defect count ($d_{\text{crit}}$):
  $$D_{\text{hist}} = \min\left(10.0, \, \frac{d_{\text{crit}}}{\max(d_{\text{all}}, 1)} \cdot 10.0 + \min(d_{\text{crit}} \cdot 1.5, 5.0)\right)$$
- $R_{\text{change}}$: Change Risk ($0-10$)
- $U_{\text{prod}}$: Production Usage / User Journey Frequency ($0-10$)
- $R_{\text{net}}$: Network Disconnection / Connection Risk ($0-10$)
- $R_{\text{unusual}}$: Unusual Behaviour Risk ($0-10$)

**Priority Classification:**
- **Critical:** $R_i \ge 8.0$
- **High:** $6.5 \le R_i < 8.0$
- **Medium:** $4.0 \le R_i < 6.5$
- **Low:** $R_i < 4.0$

---

## 🔄 3. Event State Machine Resilience & Idempotency

The online examination platform includes a stateful event engine (`AssessmentStateMachine`) to handle real-time candidate interactions under volatile network conditions.

```
                  ┌───────────────┐
                  │     IDLE      │
                  └───────┬───────┘
                          │ START_EXAM
                          ▼
                  ┌───────────────┐
           ┌─────►│    STARTED    │◄─────┐
           │      └───────┬───────┘      │
TIMER_UPDATED             │ ANSWER_SUBMITTED / SAVED
           │              ▼              │
           │      ┌───────────────┐      │ NETWORK_RECONNECTED
           └──────│   ANSWERING   ├──────┘
                  └───────┬───────┘
                          │ NETWORK_DISCONNECTED
                          ▼
                  ┌───────────────┐
                  │ DISCONNECTED  │
                  └───────────────┘
                          │ SUBMIT_EXAM
                          ▼
                  ┌───────────────┐
                  │   SUBMITTED   │ (Terminal State)
                  └───────────────┘
```

### Safety & Idempotency Guarantees
1. **Idempotency Keys:** Every event payload carries a unique `event_id`. Duplicate deliveries (e.g., retried network packets) return `DUPLICATE_REJECTED` status and do not mutate state.
2. **Out-of-Order Handling:** Events arriving before prerequisite states (e.g., `ANSWER_SUBMITTED` received before `START_EXAM`) are strictly rejected (`REJECTED`).
3. **Delayed/Stale Events:** Packets arriving after terminal state transition (`SUBMITTED`) are ignored without corrupting exam responses or timers.
4. **State Integrity:** State transitions strictly adhere to the defined state diagram; invalid transitions leave state unchanged.

---

## 📊 4. Empirical Evaluation Metric (CD/Min)

Optimizer performance is evaluated against a **FIFO (First-In, First-Out)** baseline using **Critical Defects Detected per Minute (CD/min)**:

$$\text{CD / min} = \frac{\text{Total Critical Defects Covered by Selected Portfolio}}{\text{Total Portfolio Execution Time (Minutes)}}$$

$$\text{Improvement \%} = \left(\frac{\text{CD/min}_{\text{Optimized}} - \text{CD/min}_{\text{FIFO}}}{\text{CD/min}_{\text{FIFO}}}\right) \times 100$$

- **Baseline Strategy (FIFO):** Selects test cases in sequential order ($TC001, TC002, \dots$) until budget is depleted.
- **Optimized Strategy (Risk-Based):** Selects test cases ordered by risk score / efficiency under constraints.
- **Dynamic Measurement Note:** All CD/min metrics and improvement percentages displayed on the Experiment Results page are **calculated dynamically** from live database queries on test cases and defect histories. No metrics are hardcoded.

---

## 🔒 5. Role-Based Access Control (RBAC) Matrix

| Feature / API Endpoint | Student | Tester | Test Lead | Admin |
|---|:---:|:---:|:---:|:---:|
| Take Assessment & Save Answers | ✅ (Own) | ❌ | ❌ | ❌ |
| View Test Cases & Defect History | ❌ | ✅ | ✅ | ✅ |
| Run Portfolio Optimizer (`/api/optimizer/run`) | ❌ | ✅ | ✅ | ✅ |
| Run Exact DP Optimizer (`/api/optimizer/run-dp`) | ❌ | ✅ | ✅ | ✅ |
| Apply Authorized Overrides (`/api/optimizer/override`) | ❌ | ❌ | ✅ | ✅ |
| Run Event Simulations & Experiments | ❌ | ✅ | ✅ | ✅ |
| User Management (`/api/auth/users`) | ❌ | ❌ | ❌ | ✅ |

*Ownership Enforcement:* Students can only create, answer, or submit their own assessment records (`user_id` matching JWT session token). Testers or other students attempting to alter another user's submission receive an immediate HTTP `403 Forbidden`.

---

## 🔑 6. Demo Credentials

| Role | Username | Password | Purpose |
|---|---|---|---|
| **Student** | `student1` | `student123` | Experience student exam UI, timer, autosave, submission |
| **Tester** | `tester1` | `tester123` | View risk scores, run optimizer, test event state machine |
| **Test Lead** | `testlead` | `lead123` | Run optimizer, apply priority overrides, view audit trail |
| **Admin** | `admin` | `admin123` | Full administrative control across all modules |

---

## 🚀 7. Running the Application Locally

### Prerequisites
- **Python 3.9+**
- **Node.js 18+** and `npm`

### Step 1: Backend Setup & Seeding
```bash
cd backend

# Install Python dependencies (including pytest and httpx)
pip install -r requirements.txt

# Seed the SQLite database with 35 test cases, 25 defect records, 6 users, 37 questions
python seed_data.py

# Start FastAPI dev server
uvicorn main:app --reload --port 8000
```
- Backend runs at `http://localhost:8000`
- OpenAPI Documentation: `http://localhost:8000/docs`

### Step 2: Frontend Setup
```bash
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
- Frontend application runs at `http://localhost:5173`

---

## 🧪 8. Automated Testing Suite

The repository includes a comprehensive, automated test suite built with `pytest`.

### Running All Automated Tests
```bash
cd backend

# Run the complete test suite with verbose output
python -m pytest tests/ -v
```

### Running Backend Audit Script
```bash
python test_suite.py
```

### Test Coverage Breakdown (50+ Test Scenarios)
- **`tests/test_events.py`**: State machine valid transitions, idempotency key deduplication, delayed event handling, out-of-order event rejection, and property-style deterministic sequence safety.
- **`tests/test_optimizer.py`**: Budget bounds verification, UNFEASIBLE shortfall detection, zero duplicate selections, dual objective validation, priority override integration, and Exact DP optimality gap checks.
- **`tests/test_security.py`**: Unauthenticated 401 checks, RBAC 403 enforcement for Student/Tester roles, Test Lead 200 authorization, and assessment record ownership validation.
- **`tests/test_risk.py`**: Risk score bounds $[0.0, 10.0]$, multi-factor weight sum checks, determinism, category classification, and efficiency calculations.
- **`tests/test_assessments.py`**: Assessment start/resume, answer saving, auto-grading, and double-submission prevention.

---

## 🔬 9. Running Benchmarks & Generating Workloads

### Local Optimizer Benchmarking
To compare the Greedy Heuristic against the Exact Dynamic Programming solution:
```bash
cd backend
python -m pytest tests/test_optimizer.py -k test_dp -v
```

Alternatively, invoke the API directly:
```bash
curl -X POST "http://localhost:8000/api/optimizer/run-dp" \
     -H "Content-Type: application/json" \
     -d '{"token": "test-tester-token", "time_budget_minutes": 60.0, "objective": "max_risk"}'
```

### Synthetic Workload Reseeding
To re-generate or modify synthetic test cases, defect histories, and exam questions:
```bash
cd backend

# Re-run seeder (deterministic seed ensures repeatable benchmark runs)
python seed_data.py
```
The seeder uses a deterministic random seed (`random.seed(42)`), guaranteeing that benchmark runs produce consistent, reproducible dataset distributions across environments.

---

## 📁 10. Repository Structure

```
risk-test-optimizer/
├── backend/
│   ├── main.py                  # FastAPI entry point & CORS
│   ├── database.py              # SQLite database session configuration
│   ├── models.py                # SQLAlchemy DB models
│   ├── seed_data.py             # Deterministic synthetic data seeder
│   ├── test_suite.py            # End-to-end backend verification script
│   ├── requirements.txt         # Python dependencies
│   ├── routers/
│   │   ├── auth.py              # Auth & JWT role-based session
│   │   ├── assessments.py       # Student assessment workflow APIs
│   │   ├── test_cases.py        # Test case & defect history APIs
│   │   ├── risk.py              # Explainable multi-factor risk engine
│   │   ├── optimizer.py         # Dual-objective optimizer & Exact DP endpoint
│   │   ├── events.py            # Event simulation & state machine
│   │   ├── experiments.py       # Dynamic CD/min empirical evaluation
│   │   └── security.py          # RBAC matrix & audit log APIs
│   └── tests/
│       ├── conftest.py          # Pytest fixtures & in-memory DB setup
│       ├── test_events.py       # Event state machine & idempotency tests
│       ├── test_optimizer.py    # Portfolio optimizer & DP tests
│       ├── test_security.py     # RBAC & ownership safety tests
│       ├── test_risk.py         # Risk score formula validation tests
│       └── test_assessments.py  # Assessment workflow tests
└── frontend/
    ├── src/
    │   ├── api.ts               # Axios API client layer
    │   ├── AuthContext.tsx      # Role-based auth provider
    │   ├── App.tsx              # React router & layout
    │   ├── index.css            # Global CSS design system
    │   ├── components/
    │   │   └── Sidebar.tsx      # Role-filtered sidebar
    │   └── pages/
    │       ├── Login.tsx        # Login page with quick-fill cards
    │       ├── Dashboard.tsx    # High-level metrics & charts
    │       ├── StudentAssessment.tsx # Exam workflow & simulation
    │       ├── TestCases.tsx    # Test case repository table
    │       ├── DefectHistory.tsx# Historical defect records
    │       ├── RiskAnalysis.tsx # Formula breakdown & drawer
    │       ├── Portfolio.tsx    # Portfolio optimizer UI
    │       ├── EventSimulation.tsx # State machine event trace
    │       ├── ExperimentResults.tsx # Dynamic CD/min results & limitations
    │       └── Security.tsx     # RBAC matrix & audit logs
    ├── package.json
    └── vite.config.ts
```

---

## 🎯 11. Evaluator Verification & Presentation Guide

For evaluators reviewing this repository:

1. **Verify Automated Tests:** Run `python -m pytest tests/ -v` inside `backend/` to confirm 50+ passing tests verifying state safety, idempotency, RBAC, and optimization bounds.
2. **Verify Mathematical Rigor:** Inspect `backend/routers/optimizer.py` for mathematical formulations, decision variables, greedy limitation comments, and the `POST /api/optimizer/run-dp` Exact DP comparison endpoint.
3. **Verify Dynamic CD/min Metrics:** Check `backend/routers/experiments.py` and the UI Experiment Results page to verify that CD/min improvements are computed dynamically from test case defect tables.
4. **Verify State Machine Resilience:** Open the **Event Simulation** page in the UI and click **Duplicate Event**, **Delayed Event**, and **Out-of-Order Event** to see idempotency key enforcement and step-by-step state logs in action.
