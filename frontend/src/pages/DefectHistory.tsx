import { useState, useEffect } from 'react';
import { useAuth } from '../AuthContext';
import { api } from '../api';

export default function DefectHistory() {
  const { user } = useAuth();
  const [defects, setDefects] = useState<any[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      if (!user?.token) return;
      try {
        const [dList, dSum] = await Promise.all([
          api.getDefectHistory(user.token),
          api.getDefectSummary(user.token)
        ]);
        setDefects(dList);
        setSummary(dSum);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [user]);

  if (loading) return <div className="loading">Loading historical defect records...</div>;

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Historical Defect Repository</h1>
          <p>Historical defect data collected across modules to inform risk-based prioritization.</p>
        </div>
        <span className="synthetic-label">{summary?.total_defects || 0} Total Defects</span>
      </div>

      {/* Summary Cards */}
      <div className="stats-grid">
        <div className="stat-card red">
          <div className="stat-icon">🚨</div>
          <div className="stat-value">{summary?.by_severity?.Critical || 0}</div>
          <div className="stat-label">Critical Defects</div>
        </div>

        <div className="stat-card orange">
          <div className="stat-icon">⚠️</div>
          <div className="stat-value">{summary?.by_severity?.High || 0}</div>
          <div className="stat-label">High Severity Defects</div>
        </div>

        <div className="stat-card purple">
          <div className="stat-icon">🐛</div>
          <div className="stat-value">{summary?.unresolved || 0}</div>
          <div className="stat-label">Currently Unresolved</div>
        </div>

        <div className="stat-card green">
          <div className="stat-icon">✅</div>
          <div className="stat-value">{(summary?.total_defects || 0) - (summary?.unresolved || 0)}</div>
          <div className="stat-label">Resolved Defects</div>
        </div>
      </div>

      {/* Defects Table */}
      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Defect ID</th>
              <th>Test Case ID</th>
              <th>Severity</th>
              <th>Module</th>
              <th>Description</th>
              <th>Detected Date</th>
              <th>Status</th>
              <th>MTTR (Hours)</th>
            </tr>
          </thead>
          <tbody>
            {defects.map(d => (
              <tr key={d.id}>
                <td><strong>{d.defect_id}</strong></td>
                <td><span className="badge info">{d.test_case_id}</span></td>
                <td>
                  <span className={`badge ${d.severity.toLowerCase()}`}>{d.severity}</span>
                </td>
                <td>{d.module}</td>
                <td style={{ maxWidth: '350px' }}>{d.description}</td>
                <td>{d.detected_date}</td>
                <td>
                  {d.resolved ? (
                    <span className="badge pass">Resolved</span>
                  ) : (
                    <span className="badge fail">Open</span>
                  )}
                </td>
                <td>{d.resolution_time_hours ? `${d.resolution_time_hours} hrs` : 'N/A'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
