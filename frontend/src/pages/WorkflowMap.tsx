export default function WorkflowMap() {
  const studentSteps = [
    { num: 1, title: 'Login & Authentication', desc: 'Role-based JWT session initialization' },
    { num: 2, title: 'Assessment List', desc: 'Select from available exam papers' },
    { num: 3, title: 'Instructions Page', desc: 'Review rules, duration, and scoring' },
    { num: 4, title: 'Start Exam', desc: 'State Machine transition: NOT_STARTED ➔ IN_PROGRESS' },
    { num: 5, title: 'Question Page', desc: 'Interactive Q&A palette & timer' },
    { num: 6, title: 'Answer Selection', desc: 'Autosave trigger & idempotency key creation' },
    { num: 7, title: 'Network Simulation', desc: 'Disconnect / reconnect resilience verification' },
    { num: 8, title: 'Exam Submission', desc: 'State Machine transition: IN_PROGRESS ➔ SUBMITTED' },
    { num: 9, title: 'Result Generation', desc: 'Automated evaluation & score breakdown' },
  ];

  const optimizerSteps = [
    { num: 1, title: 'Test Case Repository', desc: 'Metadata collection for 35 synthetic test cases' },
    { num: 2, title: 'Historical Defect Load', desc: 'Correlate test cases with 25 historical defect records' },
    { num: 3, title: 'Explainable Risk Scoring', desc: 'Multi-factor weighted formula (0-10 normalized score)' },
    { num: 4, title: 'Budget & Constraint Input', desc: 'Define time budget (mins) & hard/soft constraints' },
    { num: 5, title: 'Portfolio Optimization', desc: 'Dual-objective selection (Max Risk vs Max Efficiency)' },
    { num: 6, title: 'Prioritized Portfolio', desc: 'Determine which test runs First, Next, Later, or Skipped' },
    { num: 7, title: 'Authorized Override', desc: 'Test Lead priority override with mandatory audit trail' },
    { num: 8, title: 'Empirical Evaluation', desc: 'Compare Risk-based portfolio vs Baseline FIFO (CD/min)' },
  ];

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>System Architecture & Workflow Map</h1>
          <p>End-to-End Visual Workflow of both Assessment System Under Test and Test Portfolio Optimizer.</p>
        </div>
        <span className="synthetic-label">Architectural Overview</span>
      </div>

      {/* Student Workflow Map */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title" style={{ color: '#3b82f6', marginBottom: '16px' }}>
          🎓 1. Online Assessment Platform Workflow (Student Facing)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {studentSteps.map((s, idx) => (
            <div key={s.num} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '14px', background: '#f8fafc', borderRadius: '10px', border: '1px solid #e2e8f0' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#3b82f6', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '14px' }}>
                {s.num}
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: '14px', color: '#0f172a' }}>{s.title}</strong>
                <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>{s.desc}</p>
              </div>
              {idx < studentSteps.length - 1 && <span style={{ color: '#94a3b8', fontSize: '18px' }}>⬇️</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Optimizer Workflow Map */}
      <div className="card">
        <h3 className="card-title" style={{ color: '#8b5cf6', marginBottom: '16px' }}>
          🎯 2. Risk-Based Test Portfolio Optimizer Workflow (Tester / Lead Facing)
        </h3>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {optimizerSteps.map((s, idx) => (
            <div key={s.num} style={{ display: 'flex', alignItems: 'center', gap: '16px', padding: '14px', background: '#faf5ff', borderRadius: '10px', border: '1px solid #e9d5ff' }}>
              <div style={{ width: '32px', height: '32px', borderRadius: '50%', background: '#8b5cf6', color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 800, fontSize: '14px' }}>
                {s.num}
              </div>
              <div style={{ flex: 1 }}>
                <strong style={{ fontSize: '14px', color: '#0f172a' }}>{s.title}</strong>
                <p style={{ fontSize: '12px', color: '#64748b', margin: 0 }}>{s.desc}</p>
              </div>
              {idx < optimizerSteps.length - 1 && <span style={{ color: '#c084fc', fontSize: '18px' }}>⬇️</span>}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
