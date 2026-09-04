# Risk-Based Test Portfolio Optimizer for an Online Examination Platform

A full-stack, transparent, and explainable **Risk-Based Test Portfolio Optimizer** built for an **Online Assessment Platform** (System Under Test). Designed for college project presentation and evaluation.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Python 3.9+**
- **Node.js 18+** & `npm`

### 1. Backend Setup (FastAPI + SQLite)
```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Run SQLite database seeder (populates 35 test cases, 25 defect records, 6 users, 37 questions)
python seed_data.py

# Start FastAPI dev server
uvicorn main:app --reload --port 8000
```
Backend server will run at `http://localhost:8000`. Interactive API Docs are available at `http://localhost:8000/docs`.

### 2. Frontend Setup (React + TypeScript + Vite)
```bash
# Open a new terminal and navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite dev server
npm run dev
```
Frontend application will open at `http://localhost:5173`.

---

## 🎯 3-Minute Demo Script (For Project Defense / Presentation)

| Step | Time | User Role | Action | What to Point Out |
|---|---|---|---|---|
| 1 | 0:00 - 0:30 | **Student** (`student1`) | Log in as Student. Open "Student Assessment" -> Start Exam. Answer questions, simulate network disconnect & reconnect, then submit exam. | Point out **timer**, **autosave**, and **network resilience**. |
| 2 | 0:30 - 1:15 | **Tester** (`tester1`) | Log in as Tester. Open **Risk Analysis**. Point to the formula card and click a test case. | Show **multi-factor weighted formula** (0-10 normalized score). No black-box ML. |
| 3 | 1:15 - 2:00 | **Test Lead** (`testlead`) | Open **Portfolio Optimizer**. Slide budget to **60 mins**. Switch between **Max Risk** and **Max Efficiency**. Perform a priority override on a test case with reason. | Demonstrate **dual objectives**, **hard/soft constraints**, **authorized overrides**, and **audit trail**. |
| 4 | 2:00 - 2:30 | **Test Lead** (`testlead`) | Open **Event Simulation**. Click **Duplicate Event**, **Delayed Event**, and **Out-of-Order Event**. | Show **State Machine resilience**, **Idempotency keys**, and step-by-step state transition logs. |
| 5 | 2:30 - 3:00 | **Test Lead** (`testlead`) | Open **Experiment Results**. Adjust time budget. Show **Security / Access**. | Highlight **Critical Defects / Min (CD/min)** metric (measured improvement over FIFO baseline, dynamically calculated from actual data), **Error Analysis**, and **RBAC matrix**. |

---

## 🔑 Demo Credentials & Roles

| Role | Username | Password | Access Scope |
|---|---|---|---|
| **Student** | `student1` | `student123` | Take assessments, view exam instructions, autosave answers, submit exam, view results. |
| **Tester** | `tester1` | `tester123` | View test cases, defect history, risk scores, run portfolio optimizer, run event simulations. |
| **Test Lead** | `testlead` | `lead123` | All Tester privileges + **Authorized Priority Overrides** + Audit trail access. |
| **Admin** | `admin` | `admin123` | Full system access across all modules. |

---

## 📐 Explainable Risk Formula & Optimization Objectives

### 1. Multi-Factor Risk Score Formulation
The system calculates a normalized risk score between **0.0 and 10.0** using a weighted multi-factor formula:

$$\text{Risk Score} = 0.25 \times \text{Business Criticality} + 0.20 \times \text{Historical Defect Risk} + 0.20 \times \text{Change Risk} + 0.15 \times \text{Production Usage} + 0.10 \times \text{Network Risk} + 0.10 \times \text{Unusual Behaviour Risk}$$

### 2. Dual Optimization Objectives
- **Objective 1 (Max Risk Coverage):** 
  Selects test cases that maximize total cumulative risk score within time budget:
  $$\max \sum_{i \in \text{Selected}} \text{RiskScore}_i \quad \text{subject to} \sum_{i \in \text{Selected}} \text{ExecTime}_i \le \text{TimeBudget}$$
- **Objective 2 (Max Risk Efficiency):**
  Selects test cases that maximize risk detected per minute of execution time:
  $$\max \sum_{i \in \text{Selected}} \frac{\text{RiskScore}_i}{\text{ExecTime}_i}$$

---

## 📊 Empirical Evaluation Metric (CD/Min)

The baseline vs. risk-based experiment evaluates efficiency using **Critical Defects Detected per Minute**:

$$\text{CD / min} = \frac{\text{Critical Defects Detected}}{\text{Total Execution Time (Minutes)}}$$

- **Baseline Strategy (FIFO):** Executes test cases in arbitrary index order (TC001, TC002, ...).
- **Optimized Strategy (Risk-Based):** Executes test cases prioritized by risk density and constraints.
- **Results:** The CD/min improvement is **measured dynamically** from actual test case data; the Experiment Results page displays the real calculated percentage for each selected time budget. No fixed improvement percentage is assumed or hardcoded.

---

## 🔍 System Limitations & Error Analysis

1. **Cold-Start Bias:** New test cases with zero historical defects may receive artificially low initial risk scores until human testers adjust Business Criticality or Change Risk manually.
2. **Co-Dependency Gaps:** Independent greedy optimization may defer low-risk prerequisite setup test cases that high-risk test cases rely upon unless explicitly linked via Hard Constraints.
3. **Static Weights Assumption:** Weight distribution (e.g., 25% Business Criticality) is static. Extreme real-world incidents (e.g., major network outages) require manual soft-constraint toggling.

---

## 🛠️ Project Structure

```
risk-test-optimizer/
├── backend/
│   ├── main.py                  # FastAPI entry point & CORS
│   ├── database.py              # SQLite database session configuration
│   ├── models.py                # SQLAlchemy DB models (User, TestCase, Defect, Assessment, AuditLog)
│   ├── seed_data.py             # Synthetic dataset seeder script
│   ├── requirements.txt         # Python dependencies
│   └── routers/
│       ├── auth.py              # Authentication & JWT role-based session
│       ├── assessments.py       # Assessment workflow APIs (start, save, submit, result)
│       ├── test_cases.py        # Test case repository & defect history APIs
│       ├── risk.py              # Explainable risk scoring engine
│       ├── optimizer.py         # Dual-objective portfolio optimizer & override engine
│       ├── events.py            # Event simulation & state machine resilience
│       ├── experiments.py       # Empirical baseline vs optimized comparison
│       └── security.py          # RBAC matrix & audit log APIs
└── frontend/
    ├── src/
    │   ├── api.ts               # Axios API client layer
    │   ├── AuthContext.tsx      # Role-based auth provider
    │   ├── App.tsx              # React router & layout configuration
    │   ├── index.css            # Global CSS design system (Dark mode aesthetic)
    │   ├── components/
    │   │   └── Sidebar.tsx      # Role-filtered sidebar navigation
    │   └── pages/
    │       ├── Login.tsx        # Login page with quick-fill role credentials
    │       ├── Dashboard.tsx    # High-level metrics & Recharts visualizations
    │       ├── StudentAssessment.tsx # 14-stage assessment workflow & network simulation
    │       ├── TestCases.tsx    # Test case repository & filterable metadata table
    │       ├── DefectHistory.tsx# Historical defect records & severity stats
    │       ├── RiskAnalysis.tsx # Formula breakdown & raw component drawer
    │       ├── Portfolio.tsx    # Core optimizer page with budget & constraints
    │       ├── EventSimulation.tsx # Event state machine resilience trace
    │       ├── ExperimentResults.tsx # Empirical CD/min comparison & limitations
    │       ├── Security.tsx     # RBAC matrix & default deny test suite
    │       └── WorkflowMap.tsx  # Visual system workflow maps
    ├── package.json
    └── vite.config.ts
```
