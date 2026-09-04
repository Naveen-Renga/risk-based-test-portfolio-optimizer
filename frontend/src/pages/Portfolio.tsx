import { useState, useEffect } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export default function Portfolio() {
  const { user } = useAuth();
  const [budget, setBudget] = useState(60);
  const [objective, setObjective] = useState<'max_risk' | 'max_efficiency'>('max_risk');

  // Hard constraints state
  const [includeNetwork, setIncludeNetwork] = useState(true);
  const [includeSubmission, setIncludeSubmission] = useState(true);
  const [includeSecurity, setIncludeSecurity] = useState(true);

  // Soft constraints state
  const [preferHighRisk, setPreferHighRisk] = useState(true);
  const [preferRecentDefects, setPreferRecentDefects] = useState(true);
  const [preferFrequentJourneys, setPreferFrequentJourneys] = useState(true);
  const [preferShorterExecution, setPreferShorterExecution] = useState(false);

  // Optimizer result
  const [result, setResult] = useState<any>(null);

  // Override modal state
  const [overrideModal, setOverrideModal] = useState(false);
  const [selectedTc, setSelectedTc] = useState<any>(null);
  const [newPriority, setNewPriority] = useState(1);
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideLogs, setOverrideLogs] = useState<any[]>([]);

  useEffect(() => {
    runOptimization();
    loadOverrides();
  }, [budget, objective, includeNetwork, includeSubmission, includeSecurity, preferHighRisk, preferRecentDefects, preferFrequentJourneys, preferShorterExecution]);

  const runOptimization = async () => {
    try {
      const data = await api.runOptimizer({
        time_budget_minutes: budget,
        objective: objective,
        include_network_test: includeNetwork,
        include_submission_test: includeSubmission,
        include_security_test: includeSecurity,
        prefer_high_risk: preferHighRisk,
        prefer_recent_defects: preferRecentDefects,
        prefer_frequent_journeys: preferFrequentJourneys,
        prefer_shorter_execution: preferShorterExecution,
      });
      setResult(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadOverrides = async () => {
    try {
      const logs = await api.getOverrides();
      setOverrideLogs(logs);
    } catch (err) {
      console.error(err);
    }
  };

  const handleOpenOverride = (tc: any) => {
    if (user?.role !== 'test_lead' && user?.role !== 'admin') {
      alert(`ACCESS DENIED: Role '${user?.role?.toUpperCase()}' is not authorized to override recommendations. Only Test Lead or Admin can perform overrides.`);
      return;
    }
    setSelectedTc(tc);
    setNewPriority(tc.priority);
    setOverrideReason('');
    setOverrideModal(true);
  };

  const handleApplyOverride = async () => {
    if (!selectedTc || !user) return;
    if (!overrideReason.trim()) {
      alert('Override reason is required for audit logging.');
      return;
    }

    try {
      await api.override({
        token: user.token,
        test_case_id: selectedTc.test_case_id,
        old_priority: selectedTc.priority,
        new_priority: newPriority,
        reason: overrideReason,
      });
      alert(`Override successful! Priority updated for ${selectedTc.test_case_id}. Audit log entry created.`);
      setOverrideModal(false);
      loadOverrides();
      runOptimization();
    } catch (err: any) {
      alert(err.message || 'Override failed');
    }
  };

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Test Portfolio Optimizer</h1>
          <p>Core Optimizer Engine: Risk Maximization vs Risk Efficiency under Time Constraints.</p>
        </div>
        <span className="synthetic-label">Core Feature Engine</span>
      </div>

      {/* Control Panel: Budget & Objective Selection */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="grid-2" style={{ gap: '24px' }}>
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px' }}>⏱️ Testing Time Budget & Objective</h3>
            
            <div className="form-group">
              <label className="form-label">Time Budget (Minutes): <strong>{budget} mins</strong></label>
              <input
                type="range"
                min="15"
                max="120"
                step="5"
                value={budget}
                onChange={e => setBudget(Number(e.target.value))}
                style={{ width: '100%' }}
              />
              <div className="flex-between" style={{ fontSize: '11px', color: '#64748b', marginTop: '4px' }}>
                <span>15 mins (Strict)</span>
                <span>60 mins (Standard)</span>
                <span>120 mins (Full Suite)</span>
              </div>
            </div>

            <div className="form-group" style={{ marginTop: '16px' }}>
              <label className="form-label">Optimization Objective</label>
              <div className="tabs">
                <button
                  className={`tab ${objective === 'max_risk' ? 'active' : ''}`}
                  onClick={() => setObjective('max_risk')}
                >
                  🎯 Objective 1: Max Risk Coverage
                </button>
                <button
                  className={`tab ${objective === 'max_efficiency' ? 'active' : ''}`}
                  onClick={() => setObjective('max_efficiency')}
                >
                  ⚡ Objective 2: Max Risk per Minute
                </button>
              </div>
            </div>
          </div>

          {/* Constraints Selector */}
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px' }}>🔒 Hard & Soft Constraints</h3>
            
            <div style={{ marginBottom: '12px' }}>
              <span className="badge mandatory" style={{ marginBottom: '6px', display: 'inline-block' }}>Hard Constraints (Enforced)</span>
              <div className="toggle-group">
                <label className={`toggle-item ${includeNetwork ? 'active' : ''}`}>
                  <input type="checkbox" checked={includeNetwork} onChange={e => setIncludeNetwork(e.target.checked)} />
                  Network Test Required
                </label>
                <label className={`toggle-item ${includeSubmission ? 'active' : ''}`}>
                  <input type="checkbox" checked={includeSubmission} onChange={e => setIncludeSubmission(e.target.checked)} />
                  Submission Test Required
                </label>
                <label className={`toggle-item ${includeSecurity ? 'active' : ''}`}>
                  <input type="checkbox" checked={includeSecurity} onChange={e => setIncludeSecurity(e.target.checked)} />
                  Security Test Required
                </label>
              </div>
            </div>

            <div>
              <span className="badge info" style={{ marginBottom: '6px', display: 'inline-block' }}>Soft Constraints (Preferences)</span>
              <div className="toggle-group">
                <label className={`toggle-item ${preferHighRisk ? 'active' : ''}`}>
                  <input type="checkbox" checked={preferHighRisk} onChange={e => setPreferHighRisk(e.target.checked)} />
                  Prefer High Risk
                </label>
                <label className={`toggle-item ${preferRecentDefects ? 'active' : ''}`}>
                  <input type="checkbox" checked={preferRecentDefects} onChange={e => setPreferRecentDefects(e.target.checked)} />
                  Prefer High Defects
                </label>
                <label className={`toggle-item ${preferFrequentJourneys ? 'active' : ''}`}>
                  <input type="checkbox" checked={preferFrequentJourneys} onChange={e => setPreferFrequentJourneys(e.target.checked)} />
                  Prefer High Usage
                </label>
                <label className={`toggle-item ${preferShorterExecution ? 'active' : ''}`}>
                  <input type="checkbox" checked={preferShorterExecution} onChange={e => setPreferShorterExecution(e.target.checked)} />
                  Prefer Short Exec
                </label>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Warnings / Violations */}
      {result?.hard_constraint_violations?.map((v: string, i: number) => (
        <div key={i} className="warning-box">
          ⚠️ {v}
        </div>
      ))}

      {/* Metrics Banner */}
      <div className="stats-grid">
        <div className="stat-card green">
          <div className="stat-icon">✅</div>
          <div className="stat-value">{result?.selected_count || 0} / {result?.total_test_cases || 0}</div>
          <div className="stat-label">Selected Test Cases</div>
        </div>

        <div className="stat-card blue">
          <div className="stat-icon">⏱️</div>
          <div className="stat-value">{result?.total_execution_time || 0}m</div>
          <div className="stat-label">Total Execution Time</div>
        </div>

        <div className="stat-card purple">
          <div className="stat-icon">🛡️</div>
          <div className="stat-value">{result?.risk_coverage_percent || 0}%</div>
          <div className="stat-label">Risk Score Coverage</div>
        </div>

        <div className="stat-card red">
          <div className="stat-icon">🚨</div>
          <div className="stat-value">{result?.critical_defect_coverage_percent || 0}%</div>
          <div className="stat-label">Critical Defect Coverage</div>
        </div>
      </div>

      {/* Recommended Portfolio Table */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="card-header">
          <h3 className="card-title">
            📋 Recommended Test Execution Portfolio ({result?.objective_label})
          </h3>
          <span style={{ fontSize: '12px', color: '#64748b' }}>
            Answer: Which test should be executed first, next, later, or skipped?
          </span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Priority</th>
                <th>ID</th>
                <th>Test Case Name</th>
                <th>Journey</th>
                <th>Risk Score</th>
                <th>Exec Time</th>
                <th>Efficiency (R/min)</th>
                <th>Selection Reason</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {result?.selected?.map((tc: any) => (
                <tr key={tc.test_case_id}>
                  <td>
                    <span className={`priority-num ${tc.priority <= 3 ? 'p' + tc.priority : 'default'}`}>
                      {tc.priority}
                    </span>
                  </td>
                  <td><strong>{tc.test_case_id}</strong></td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{tc.name}</div>
                    {tc.is_mandatory && <span className="badge mandatory" style={{ fontSize: '9px' }}>Mandatory</span>}
                  </td>
                  <td><span className="badge info">{tc.critical_user_journey}</span></td>
                  <td>
                    <strong style={{ color: tc.risk_score >= 8 ? '#dc2626' : '#ea580c' }}>
                      {tc.risk_score}
                    </strong>
                  </td>
                  <td>⏱️ {tc.execution_time_minutes} min</td>
                  <td><strong>{tc.efficiency_score}</strong></td>
                  <td style={{ fontSize: '11px', color: '#475569', maxWidth: '240px' }}>{tc.reason}</td>
                  <td>
                    <button
                      className="btn btn-secondary btn-sm"
                      onClick={() => handleOpenOverride(tc)}
                      title="Test Lead Authorized Override"
                    >
                      👑 Override
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Deferred Test Cases */}
      {result?.deferred && result.deferred.length > 0 && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 className="card-title" style={{ color: '#64748b', marginBottom: '12px' }}>
            ⏳ Deferred Test Cases ({result.deferred.length} Excluded by Budget/Priority)
          </h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Rank</th>
                  <th>ID</th>
                  <th>Test Case Name</th>
                  <th>Risk Score</th>
                  <th>Time</th>
                  <th>Reason Deferred</th>
                </tr>
              </thead>
              <tbody>
                {result.deferred.map((tc: any) => (
                  <tr key={tc.test_case_id} style={{ opacity: 0.7 }}>
                    <td>#{tc.priority}</td>
                    <td>{tc.test_case_id}</td>
                    <td>{tc.name}</td>
                    <td>{tc.risk_score}</td>
                    <td>{tc.execution_time_minutes} min</td>
                    <td style={{ fontSize: '11px', color: '#94a3b8' }}>Exceeds remaining time budget ({budget} min limit)</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Override Audit Logs */}
      {overrideLogs.length > 0 && (
        <div className="card">
          <h3 className="card-title" style={{ marginBottom: '12px' }}>📜 Authorized Priority Override Audit Trail</h3>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Test Case</th>
                  <th>Old Priority</th>
                  <th>New Priority</th>
                  <th>Override Reason</th>
                  <th>Performed By</th>
                  <th>Role</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {overrideLogs.map((l: any) => (
                  <tr key={l.id}>
                    <td><strong>{l.test_case_id}</strong></td>
                    <td>#{l.old_priority}</td>
                    <td><span className="badge critical">#{l.new_priority}</span></td>
                    <td>{l.reason}</td>
                    <td>{l.performed_by}</td>
                    <td><span className="badge mandatory">{l.role}</span></td>
                    <td>{l.timestamp}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Override Modal */}
      {overrideModal && selectedTc && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
          background: 'rgba(0,0,0,0.6)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }}>
          <div className="card" style={{ width: '480px', padding: '28px' }}>
            <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '4px' }}>👑 Authorized Priority Override</h2>
            <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '20px' }}>
              Override optimizer recommendation for <code>{selectedTc.test_case_id}</code>. Mandatory audit logging will occur.
            </p>

            <div className="form-group">
              <label className="form-label">Current Recommended Priority</label>
              <input type="text" className="form-input" value={`#${selectedTc.priority} (${selectedTc.name})`} disabled />
            </div>

            <div className="form-group">
              <label className="form-label">New Priority Rank</label>
              <input
                type="number"
                min="1"
                max={result?.total_test_cases || 35}
                className="form-input"
                value={newPriority}
                onChange={e => setNewPriority(Number(e.target.value))}
              />
            </div>

            <div className="form-group">
              <label className="form-label">Override Justification (Required for Audit)</label>
              <textarea
                className="form-textarea"
                rows={3}
                placeholder="e.g. Test network environment unavailable for TC007 until 3 PM..."
                value={overrideReason}
                onChange={e => setOverrideReason(e.target.value)}
              />
            </div>

            <div className="flex-between" style={{ marginTop: '20px' }}>
              <button className="btn btn-secondary" onClick={() => setOverrideModal(false)}>Cancel</button>
              <button className="btn btn-primary" onClick={handleApplyOverride}>Confirm Authorized Override</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
