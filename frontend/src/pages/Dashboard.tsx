import { useEffect, useState } from 'react';
import { api } from '../api';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from 'recharts';

export default function Dashboard() {
  const [stats, setStats] = useState<any>(null);
  const [optimizerStats, setOptimizerStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [dashStats, optData] = await Promise.all([
          api.getDashboardStats(),
          api.runOptimizer({ time_budget_minutes: 60, objective: 'max_risk' })
        ]);
        setStats(dashStats);
        setOptimizerStats(optData);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) return <div className="loading">Loading system metrics and risk analytics...</div>;

  const COLORS = ['#ef4444', '#ea580c', '#ca8a04', '#16a34a'];

  const riskPieData = stats?.risk_distribution
    ? Object.entries(stats.risk_distribution).map(([name, value]) => ({ name, value }))
    : [];

  const moduleData = stats?.modules
    ? Object.entries(stats.modules).map(([name, data]: [string, any]) => ({
        name,
        tests: data.test_count,
        defects: data.total_defects,
        criticalDefects: data.critical_defects,
      }))
    : [];

  const journeyData = stats?.journeys
    ? Object.entries(stats.journeys).map(([name, data]: [string, any]) => ({
        name: name.length > 15 ? name.substring(0, 15) + '...' : name,
        usage: data.avg_usage,
      }))
    : [];

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>System Overview & Dashboard</h1>
          <p>Online Assessment Platform System Under Test + Risk Portfolio Optimizer Metrics</p>
        </div>
        <span className="synthetic-label">⚡ Synthetic Dataset Loaded</span>
      </div>

      {/* Top Stat Cards */}
      <div className="stats-grid">
        <div className="stat-card blue">
          <div className="stat-icon">🧪</div>
          <div className="stat-value">{stats?.total_test_cases || 0}</div>
          <div className="stat-label">Total Test Cases</div>
        </div>

        <div className="stat-card red">
          <div className="stat-icon">🚨</div>
          <div className="stat-value">{stats?.critical_tests || 0}</div>
          <div className="stat-label">Critical Priority Tests</div>
        </div>

        <div className="stat-card orange">
          <div className="stat-icon">⚠️</div>
          <div className="stat-value">{stats?.high_risk_tests || 0}</div>
          <div className="stat-label">High Risk Tests</div>
        </div>

        <div className="stat-card purple">
          <div className="stat-icon">📊</div>
          <div className="stat-value">{stats?.average_risk_score || 0} / 10</div>
          <div className="stat-label">Average Risk Score</div>
        </div>

        <div className="stat-card green">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{optimizerStats?.selected_count || 0}</div>
          <div className="stat-label">Selected Tests (60m Budget)</div>
        </div>

        <div className="stat-card cyan">
          <div className="stat-icon">🛡️</div>
          <div className="stat-value">{optimizerStats?.risk_coverage_percent || 0}%</div>
          <div className="stat-label">Risk Coverage</div>
        </div>
      </div>

      {/* Charts Grid */}
      <div className="charts-grid">
        {/* Risk Distribution Pie Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Test Portfolio Risk Distribution</h3>
          <ResponsiveContainer width="100%" height={260}>
            <PieChart>
              <Pie data={riskPieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={90} label={entry => `${entry.name}: ${entry.value}`}>
                {riskPieData.map((_, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Module Defects Bar Chart */}
        <div className="chart-card">
          <h3 className="chart-title">Module Defect Density & Test Count</h3>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={moduleData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="tests" fill="#3b82f6" name="Test Cases" />
              <Bar dataKey="defects" fill="#f59e0b" name="Total Defects" />
              <Bar dataKey="criticalDefects" fill="#ef4444" name="Critical Defects" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Usage & Coverage Row */}
      <div className="charts-grid">
        <div className="chart-card">
          <h3 className="chart-title">Production Usage by Critical User Journey</h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={journeyData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis type="number" domain={[0, 10]} />
              <YAxis dataKey="name" type="category" width={140} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="usage" fill="#8b5cf6" name="Usage Score (0-10)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3 className="chart-title">Optimizer Risk vs Time Coverage</h3>
          <div style={{ padding: '20px', background: '#f8fafc', borderRadius: '10px', marginTop: '10px' }}>
            <div style={{ marginBottom: '16px' }}>
              <div className="flex-between" style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                <span>Risk Coverage</span>
                <span>{optimizerStats?.risk_coverage_percent}%</span>
              </div>
              <div style={{ background: '#e2e8f0', borderRadius: '6px', height: '12px', overflow: 'hidden' }}>
                <div style={{ width: `${optimizerStats?.risk_coverage_percent}%`, background: 'linear-gradient(90deg, #3b82f6, #8b5cf6)', height: '100%' }} />
              </div>
            </div>

            <div style={{ marginBottom: '16px' }}>
              <div className="flex-between" style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                <span>Critical Defect Coverage</span>
                <span>{optimizerStats?.critical_defect_coverage_percent}%</span>
              </div>
              <div style={{ background: '#e2e8f0', borderRadius: '6px', height: '12px', overflow: 'hidden' }}>
                <div style={{ width: `${optimizerStats?.critical_defect_coverage_percent}%`, background: 'linear-gradient(90deg, #ef4444, #f59e0b)', height: '100%' }} />
              </div>
            </div>

            <div>
              <div className="flex-between" style={{ fontSize: '13px', fontWeight: 600, marginBottom: '6px' }}>
                <span>Time Budget Utilization</span>
                <span>{optimizerStats?.total_execution_time} / 60.0 mins</span>
              </div>
              <div style={{ background: '#e2e8f0', borderRadius: '6px', height: '12px', overflow: 'hidden' }}>
                <div style={{ width: `${(optimizerStats?.total_execution_time / 60) * 100}%`, background: '#10b981', height: '100%' }} />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
