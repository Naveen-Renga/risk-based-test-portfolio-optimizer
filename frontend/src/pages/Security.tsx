import { useState, useEffect } from 'react';
import { api } from '../api';
import { useAuth } from '../AuthContext';

export default function Security() {
  const { user } = useAuth();
  const [demoResults, setDemoResults] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [permissions, setPermissions] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSecurityData();
  }, []);

  const loadSecurityData = async () => {
    setLoading(true);
    try {
      const [demo, sLogs, perms] = await Promise.all([
        api.securityDemo(),
        api.getSecurityLogs(),
        api.getPermissions()
      ]);
      setDemoResults(demo);
      setLogs(sLogs);
      setPermissions(perms);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTestCheck = async (action: string) => {
    if (!user) return;
    try {
      const res = await api.securityCheck(user.token, action);
      alert(`Security Check Result: ${res.result}\nUser: ${res.user} (${res.role})\nAction: ${res.action}\nReason: ${res.reason}`);
      loadSecurityData();
    } catch (err: any) {
      alert(err.message || 'Check failed');
    }
  };

  if (loading && !demoResults) return <div className="loading">Running security suite and permission matrix...</div>;

  return (
    <div>
      <div className="page-header flex-between">
        <div>
          <h1>Security Controls & Secure Defaults</h1>
          <p>Demonstrating Role-Based Access Control (RBAC), unauthorized action prevention, and audit logging.</p>
        </div>
        <span className="synthetic-label">Security Engine</span>
      </div>

      {/* Current User Session Badge */}
      <div className="card" style={{ marginBottom: '24px', background: 'linear-gradient(135deg, #0f172a, #1e293b)', color: 'white' }}>
        <div className="flex-between">
          <div>
            <div style={{ fontSize: '12px', textTransform: 'uppercase', color: '#94a3b8' }}>Active Session Token Context</div>
            <h2 style={{ fontSize: '20px', fontWeight: 800, marginTop: '4px' }}>
              Logged in as: <span style={{ color: '#60a5fa' }}>{user?.full_name}</span> (Role: <code>{user?.role?.toUpperCase()}</code>)
            </h2>
          </div>

          <div className="flex-gap">
            <button className="btn btn-primary btn-sm" onClick={() => handleTestCheck('portfolio_override')}>
              Test Override Access
            </button>
            <button className="btn btn-secondary btn-sm" onClick={() => handleTestCheck('admin_config')}>
              Test Admin Config Access
            </button>
          </div>
        </div>
      </div>

      {/* Permission Matrix */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <h3 className="card-title" style={{ marginBottom: '12px' }}>🔒 Role-Based Access Control (RBAC) Matrix</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Action / Feature</th>
                <th>Student</th>
                <th>Tester</th>
                <th>Test Lead</th>
                <th>Admin</th>
              </tr>
            </thead>
            <tbody>
              {permissions && Object.entries(permissions).map(([action, allowedRoles]: [string, any]) => (
                <tr key={action}>
                  <td><strong><code>{action}</code></strong></td>
                  <td>{allowedRoles.includes('student') ? '✅ ALLOWED' : '❌ DENIED'}</td>
                  <td>{allowedRoles.includes('tester') ? '✅ ALLOWED' : '❌ DENIED'}</td>
                  <td>{allowedRoles.includes('test_lead') ? '✅ ALLOWED' : '❌ DENIED'}</td>
                  <td>{allowedRoles.includes('admin') ? '✅ ALLOWED' : '❌ DENIED'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Automated Security Demo Scenarios */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div className="flex-between" style={{ marginBottom: '12px' }}>
          <h3 className="card-title">🧪 Automated Security Misuse & Default Deny Suite</h3>
          <span className="badge pass">{demoResults?.passed} / {demoResults?.total_scenarios} Tests Passed</span>
        </div>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Role Attempting Action</th>
                <th>Action Attempted</th>
                <th>Expected Result</th>
                <th>Actual Result</th>
                <th>Enforcement Status</th>
              </tr>
            </thead>
            <tbody>
              {demoResults?.results?.map((res: any, idx: number) => (
                <tr key={idx}>
                  <td><span className="badge info">{res.role}</span></td>
                  <td><code>{res.action}</code></td>
                  <td><span className={`badge ${res.expected === 'ALLOWED' ? 'pass' : 'fail'}`}>{res.expected}</span></td>
                  <td><span className={`badge ${res.actual === 'ALLOWED' ? 'pass' : 'fail'}`}>{res.actual}</span></td>
                  <td>
                    {res.passed ? (
                      <span style={{ color: '#16a34a', fontWeight: 600 }}>✅ PASS (Secured)</span>
                    ) : (
                      <span style={{ color: '#dc2626', fontWeight: 600 }}>❌ FAIL</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Security Audit Log */}
      <div className="card">
        <h3 className="card-title" style={{ marginBottom: '12px' }}>📜 Security Audit Logs</h3>
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Action Attempted</th>
                <th>Result</th>
                <th>Reason / Detail</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l: any) => (
                <tr key={l.id}>
                  <td><strong>{l.user}</strong></td>
                  <td><span className="badge info">{l.role}</span></td>
                  <td><code>{l.action}</code></td>
                  <td>
                    <span className={`badge ${l.result === 'ALLOWED' ? 'pass' : 'fail'}`}>{l.result}</span>
                  </td>
                  <td style={{ fontSize: '11px', color: '#475569' }}>{l.reason}</td>
                  <td style={{ fontSize: '11px' }}>{l.timestamp}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
