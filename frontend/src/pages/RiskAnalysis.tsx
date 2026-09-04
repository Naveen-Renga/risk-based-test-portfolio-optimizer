import { useState, useEffect } from 'react';
import { api } from '../api';

export default function RiskAnalysis() {
  const [riskScores, setRiskScores] = useState<any[]>([]);
  const [formula, setFormula] = useState<any>(null);
  const [selectedTestCase, setSelectedTestCase] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [scores, form] = await Promise.all([
          api.getRiskScores(),
          api.getRiskFormula()
        ]);
        setRiskScores(scores);
        setFormula(form);
        if (scores.length > 0) setSelectedTestCase(scores[0]);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="loading">Calculating risk models and factors...</div>;

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Explainable Risk Scoring Engine</h1>
          <p>Transparent multi-factor risk formulation (0-10 normalized scale). No black-box ML.</p>
        </div>
        <span className="synthetic-label">Transparent Algorithm</span>
      </div>

      {/* Formula Explanation Banner */}
      <div className="card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: 'white' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 700, color: '#60a5fa', marginBottom: '8px' }}>
          📐 Explainable Risk Formula
        </h3>
        <div style={{ fontSize: '15px', fontWeight: 600, fontFamily: 'monospace', background: 'rgba(255,255,255,0.06)', padding: '14px', borderRadius: '8px', marginBottom: '16px' }}>
          {formula?.formula}
        </div>

        <div className="grid-3" style={{ fontSize: '12px' }}>
          <div>🎯 <strong>0.25</strong> × Business Criticality</div>
          <div>🐛 <strong>0.20</strong> × Historical Defect Risk</div>
          <div>🔄 <strong>0.20</strong> × Change Risk</div>
          <div>📊 <strong>0.15</strong> × Production Usage</div>
          <div>🌐 <strong>0.10</strong> × Network Risk</div>
          <div>⚡ <strong>0.10</strong> × Unusual Behaviour Risk</div>
        </div>
      </div>

      {/* Selected Test Case Breakdown Drawer */}
      {selectedTestCase && (
        <div className="card" style={{ marginBottom: '24px', border: '2px solid #3b82f6' }}>
          <div className="card-header">
            <h3 className="card-title">
              🔍 Detailed Factor Calculation Breakdown: <code>{selectedTestCase.test_case_id}</code> - {selectedTestCase.name}
            </h3>
            <span className={`badge ${selectedTestCase.priority_category.toLowerCase()}`}>
              {selectedTestCase.priority_category} ({selectedTestCase.risk_score} / 10)
            </span>
          </div>

          <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '16px' }}>
            Primary Driver: <strong>{selectedTestCase.reason}</strong>
          </p>

          {/* Component Bars */}
          <div className="grid-2">
            {Object.entries(selectedTestCase.components || {}).map(([key, comp]: [string, any]) => {
              const label = key.replace(/_/g, ' ').toUpperCase();
              const weightedContribution = (comp.value * comp.weight).toFixed(2);

              return (
                <div key={key} style={{ background: '#f8fafc', padding: '12px 16px', borderRadius: '8px', border: '1px solid #e2e8f0' }}>
                  <div className="flex-between" style={{ fontSize: '12px', fontWeight: 600, marginBottom: '4px' }}>
                    <span>{label}</span>
                    <span>Raw: {comp.value} × {comp.weight} = +{weightedContribution} pts</span>
                  </div>
                  <div style={{ background: '#e2e8f0', height: '8px', borderRadius: '4px', overflow: 'hidden' }}>
                    <div style={{ width: `${(comp.value / 10) * 100}%`, height: '100%', background: '#3b82f6' }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Risk Scores Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Test Case Name</th>
              <th>Risk Score</th>
              <th>Category</th>
              <th>Crit (25%)</th>
              <th>Defect (20%)</th>
              <th>Change (20%)</th>
              <th>Usage (15%)</th>
              <th>Net (10%)</th>
              <th>Unusual (10%)</th>
              <th>Primary Driver Reason</th>
            </tr>
          </thead>
          <tbody>
            {riskScores.map(r => (
              <tr
                key={r.test_case_id}
                style={{ cursor: 'pointer', background: selectedTestCase?.test_case_id === r.test_case_id ? '#eff6ff' : '' }}
                onClick={() => setSelectedTestCase(r)}
              >
                <td><strong>{r.test_case_id}</strong></td>
                <td><span style={{ fontWeight: 600 }}>{r.name}</span></td>
                <td>
                  <span className="score-pill" style={{ color: r.risk_score >= 8 ? '#dc2626' : r.risk_score >= 6 ? '#ea580c' : '#16a34a' }}>
                    {r.risk_score}
                  </span>
                </td>
                <td><span className={`badge ${r.priority_category.toLowerCase()}`}>{r.priority_category}</span></td>
                <td>{r.components?.business_criticality?.value}</td>
                <td>{r.components?.historical_defect_risk?.value}</td>
                <td>{r.components?.change_risk?.value}</td>
                <td>{r.components?.production_usage?.value}</td>
                <td>{r.components?.network_risk?.value}</td>
                <td>{r.components?.unusual_behaviour_risk?.value}</td>
                <td style={{ fontSize: '11px', color: '#475569' }}>{r.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
