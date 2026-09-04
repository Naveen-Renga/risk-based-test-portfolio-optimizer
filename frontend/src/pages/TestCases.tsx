import { useState, useEffect } from 'react';
import { api } from '../api';

export default function TestCases() {
  const [testCases, setTestCases] = useState<any[]>([]);
  const [riskScores, setRiskScores] = useState<Record<string, any>>({});
  const [filterModule, setFilterModule] = useState('All');
  const [filterCategory, setFilterCategory] = useState('All');
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const [tcs, risks] = await Promise.all([
          api.getTestCases(),
          api.getRiskScores()
        ]);
        setTestCases(tcs);

        const rMap: Record<string, any> = {};
        risks.forEach((r: any) => { rMap[r.test_case_id] = r; });
        setRiskScores(rMap);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  if (loading) return <div className="loading">Loading 35+ assessment platform test cases...</div>;

  const modules = ['All', ...Array.from(new Set(testCases.map(t => t.module)))];
  const categories = ['All', 'Critical', 'High', 'Medium', 'Low'];

  const filtered = testCases.filter(tc => {
    const risk = riskScores[tc.test_case_id];
    const matchesModule = filterModule === 'All' || tc.module === filterModule;
    const matchesCategory = filterCategory === 'All' || risk?.priority_category === filterCategory;
    const matchesSearch = search === '' ||
      tc.test_case_id.toLowerCase().includes(search.toLowerCase()) ||
      tc.name.toLowerCase().includes(search.toLowerCase()) ||
      tc.critical_user_journey.toLowerCase().includes(search.toLowerCase());
    return matchesModule && matchesCategory && matchesSearch;
  });

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Test Case Portfolio Repository</h1>
          <p>Metadata repository for 35 synthetic test cases correlated with the assessment workflow.</p>
        </div>
        <span className="synthetic-label">35 Test Cases</span>
      </div>

      {/* Filter Bar */}
      <div className="card" style={{ marginBottom: '20px', padding: '16px 20px' }}>
        <div className="grid-3" style={{ alignItems: 'end' }}>
          <div>
            <label className="form-label">Search Test Case</label>
            <input
              type="text"
              className="form-input"
              placeholder="Search by ID, name, or journey..."
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
          <div>
            <label className="form-label">Filter by Module</label>
            <select className="form-select" value={filterModule} onChange={e => setFilterModule(e.target.value)}>
              {modules.map(m => <option key={m} value={m}>{m}</option>)}
            </select>
          </div>
          <div>
            <label className="form-label">Filter by Risk Priority</label>
            <select className="form-select" value={filterCategory} onChange={e => setFilterCategory(e.target.value)}>
              {categories.map(c => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Test Cases Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Test Case Name</th>
              <th>Module</th>
              <th>Critical Journey</th>
              <th>Risk Score</th>
              <th>Priority</th>
              <th>Exec Time</th>
              <th>Criticality</th>
              <th>Defects</th>
              <th>Mandatory</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map(tc => {
              const risk = riskScores[tc.test_case_id];
              const score = risk?.risk_score || 0;
              const category = risk?.priority_category || 'Low';

              return (
                <tr key={tc.id}>
                  <td><strong>{tc.test_case_id}</strong></td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{tc.name}</div>
                    <div style={{ fontSize: '11px', color: '#64748b' }}>{tc.description}</div>
                  </td>
                  <td><span className="badge info">{tc.module}</span></td>
                  <td><span style={{ fontSize: '12px', fontWeight: 500 }}>{tc.critical_user_journey}</span></td>
                  <td>
                    <div className="score-pill">
                      <div className="risk-bar">
                        <div
                          className="risk-bar-fill"
                          style={{
                            width: `${(score / 10) * 100}%`,
                            background: score >= 8 ? '#ef4444' : score >= 6 ? '#ea580c' : score >= 4 ? '#ca8a04' : '#16a34a'
                          }}
                        />
                      </div>
                      {score}
                    </div>
                  </td>
                  <td>
                    <span className={`badge ${category.toLowerCase()}`}>{category}</span>
                  </td>
                  <td>⏱️ {tc.execution_time_minutes} min</td>
                  <td>⭐ {tc.business_criticality}/10</td>
                  <td>🐛 {tc.historical_defect_count} ({tc.historical_critical_defect_count} crit)</td>
                  <td>
                    {tc.is_mandatory ? (
                      <span className="badge mandatory">Mandatory</span>
                    ) : (
                      <span style={{ color: '#94a3b8', fontSize: '12px' }}>Optional</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
