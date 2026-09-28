import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { api } from '../api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function ExperimentResults() {
  const { user } = useAuth();
  const [budget, setBudget] = useState(60);
  const [expData, setExpData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    runExperiment();
  }, [budget, user]);

  const runExperiment = async () => {
    if (!user?.token) return;
    setLoading(true);
    try {
      const data = await api.runExperiment(budget, user.token);
      setExpData(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && !expData) return <div className="loading">Running baseline vs optimized comparison experiment...</div>;

  const comparisonChartData = [
    {
      name: 'Baseline (FIFO)',
      criticalDefects: expData?.baseline?.critical_defects_detected || 0,
      cdPerMin: expData?.baseline?.cd_per_minute || 0,
      execTime: expData?.baseline?.total_execution_time || 0,
    },
    {
      name: 'Optimized (Risk)',
      criticalDefects: expData?.optimized?.critical_defects_detected || 0,
      cdPerMin: expData?.optimized?.cd_per_minute || 0,
      execTime: expData?.optimized?.total_execution_time || 0,
    },
  ];

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Empirical Experiment Results</h1>
          <p>Baseline Testing vs Risk-Based Optimized Testing (Evaluation Metric: Critical Defects Detected / Minute).</p>
        </div>
        <span className="synthetic-label">Dynamic Calculation</span>
      </div>

      {/* Budget Slider */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="flex-between">
          <div>
            <h3 style={{ fontSize: '15px', fontWeight: 700 }}>⏱️ Time Budget Constraint: {budget} minutes</h3>
            <p style={{ fontSize: '12px', color: '#64748b' }}>Change time budget to see dynamic recalculation of metrics across both strategies.</p>
          </div>
          <div style={{ width: '300px' }}>
            <input
              type="range"
              min="15"
              max="120"
              step="5"
              value={budget}
              onChange={e => setBudget(Number(e.target.value))}
              style={{ width: '100%' }}
            />
          </div>
        </div>
      </div>

      {/* Formula & Improvement Highlight */}
      <div className="card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: 'white' }}>
        <div className="flex-between">
          <div>
            <div style={{ fontSize: '12px', textTransform: 'uppercase', color: '#60a5fa', fontWeight: 600, letterSpacing: '0.5px' }}>
              Primary Evaluation Formula
            </div>
            <div style={{ fontSize: '18px', fontWeight: 800, fontFamily: 'monospace', margin: '6px 0' }}>
              Critical-Defect Detection per Minute = Critical Defects Detected / Execution Time (mins)
            </div>
          </div>

          <div style={{ textAlign: 'right', background: 'rgba(16, 185, 129, 0.15)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '12px 24px', borderRadius: '12px' }}>
            <div style={{ fontSize: '32px', fontWeight: 800, color: '#34d399' }}>
              +{expData?.improvement?.cd_per_min_improvement_percent}%
            </div>
            <div style={{ fontSize: '11px', color: '#a7f3d0', fontWeight: 600 }}>CD/Min Improvement</div>
          </div>
        </div>
      </div>

      {/* Side-by-Side Comparison */}
      <div className="comparison-grid" style={{ marginBottom: '24px' }}>
        {/* Baseline Card */}
        <div className="comparison-card baseline">
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <h3>Baseline Testing (FIFO Strategy)</h3>
            <span className="badge warning">Conventional</span>
          </div>

          <div className="metric-row">
            <span>Tests Executed:</span>
            <span className="metric-value">{expData?.baseline?.tests_executed} tests</span>
          </div>

          <div className="metric-row">
            <span>Execution Time:</span>
            <span className="metric-value">{expData?.baseline?.total_execution_time} mins</span>
          </div>

          <div className="metric-row">
            <span>Critical Defects Caught:</span>
            <span className="metric-value" style={{ color: '#ea580c' }}>{expData?.baseline?.critical_defects_detected} defects</span>
          </div>

          <div className="metric-row" style={{ borderBottom: 'none', paddingTop: '12px' }}>
            <span style={{ fontSize: '15px', fontWeight: 700 }}>Critical Defects / Min:</span>
            <span className="metric-value" style={{ fontSize: '20px', color: '#ea580c' }}>
              {expData?.baseline?.cd_per_minute}
            </span>
          </div>
        </div>

        {/* Optimized Card */}
        <div className="comparison-card optimized">
          <div className="flex-between" style={{ marginBottom: '12px' }}>
            <h3>Optimized Testing (Risk-Based Portfolio)</h3>
            <span className="badge pass">Portfolio Optimizer</span>
          </div>

          <div className="metric-row">
            <span>Tests Executed:</span>
            <span className="metric-value">{expData?.optimized?.tests_executed} tests</span>
          </div>

          <div className="metric-row">
            <span>Execution Time:</span>
            <span className="metric-value">{expData?.optimized?.total_execution_time} mins</span>
          </div>

          <div className="metric-row">
            <span>Critical Defects Caught:</span>
            <span className="metric-value" style={{ color: '#16a34a' }}>{expData?.optimized?.critical_defects_detected} defects</span>
          </div>

          <div className="metric-row" style={{ borderBottom: 'none', paddingTop: '12px' }}>
            <span style={{ fontSize: '15px', fontWeight: 700 }}>Critical Defects / Min:</span>
            <span className="metric-value" style={{ fontSize: '20px', color: '#16a34a' }}>
              {expData?.optimized?.cd_per_minute}
            </span>
          </div>
        </div>
      </div>

      {/* Chart */}
      <div className="chart-card" style={{ marginBottom: '24px' }}>
        <h3 className="chart-title">Visual Comparison: Critical Defects vs Efficiency</h3>
        <ResponsiveContainer width="100%" height={260}>
          <BarChart data={comparisonChartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey="criticalDefects" fill="#ef4444" name="Critical Defects Detected" />
            <Bar dataKey="cdPerMin" fill="#10b981" name="CD / Minute" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Error Analysis & Limitations */}
      <div className="card">
        <h3 className="card-title" style={{ color: '#dc2626', marginBottom: '12px' }}>
          🔍 Error Analysis & Risk-Based Limitations Discussion
        </h3>
        <p style={{ color: '#64748b', fontSize: '13px', marginBottom: '16px' }}>
          Section 16 requirement: Explicit analysis of cases where risk-based optimization might make poor decisions or miss uncaptured critical defects.
        </p>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {expData?.error_analysis?.limitations?.map((lim: any, idx: number) => (
            <div key={idx} style={{ padding: '14px', background: '#fff7ed', border: '1px solid #ffedd5', borderRadius: '8px' }}>
              <strong style={{ color: '#c2410c', fontSize: '14px' }}>Limitation #{idx + 1}: {lim.title}</strong>
              <p style={{ color: '#475569', fontSize: '13px', marginTop: '4px' }}>{lim.description}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
