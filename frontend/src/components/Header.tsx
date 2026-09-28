import { useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../AuthContext';

export default function Header() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  // Map route paths to friendly title
  const getPageTitle = (path: string) => {
    switch (path) {
      case '/dashboard': return 'System Overview & Dashboard';
      case '/assessment': return 'Student Online Assessment';
      case '/test-cases': return 'Test Case Repository';
      case '/defect-history': return 'Historical Defect Repository';
      case '/risk-analysis': return 'Explainable Risk Scoring Analysis';
      case '/portfolio': return 'Test Portfolio Optimizer';
      case '/experiments': return 'Empirical Experiment Results';
      case '/events': return 'Event Simulation & State Machine';
      case '/security': return 'Security & Role-Based Access';
      case '/workflow': return 'System Workflow Map';
      default: return 'Online Assessment & Risk Optimizer';
    }
  };

  return (
    <header style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      padding: '14px 24px',
      background: 'rgba(30, 41, 59, 0.95)',
      backdropFilter: 'blur(8px)',
      borderBottom: '1px solid #334155',
      marginBottom: '20px',
      borderRadius: '12px'
    }}>
      {/* Left: Back button & Page Title */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <button
          onClick={() => navigate(-1)}
          className="btn btn-secondary btn-sm"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: '#334155',
            color: '#f8fafc',
            border: '1px solid #475569',
            fontWeight: 600,
            cursor: 'pointer',
            padding: '6px 14px',
            borderRadius: '6px'
          }}
          title="Go back to previous page"
        >
          ⬅️ Back
        </button>
        <span style={{ fontSize: '15px', fontWeight: 700, color: '#f8fafc' }}>
          {getPageTitle(location.pathname)}
        </span>
      </div>

      {/* Right: User Role & Mandatory Logout Button */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#0f172a', padding: '4px 12px', borderRadius: '20px', border: '1px solid #334155' }}>
          <span style={{ fontSize: '13px', fontWeight: 600, color: '#38bdf8' }}>👤 {user?.full_name}</span>
          <span className="badge info" style={{ fontSize: '10px', textTransform: 'uppercase' }}>
            {user?.role?.replace('_', ' ')}
          </span>
        </div>

        <button
          onClick={handleLogout}
          className="btn btn-danger btn-sm"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            fontWeight: 700,
            cursor: 'pointer',
            padding: '6px 16px',
            borderRadius: '6px'
          }}
          title="Sign out of system"
        >
          🚪 Logout
        </button>
      </div>
    </header>
  );
}
