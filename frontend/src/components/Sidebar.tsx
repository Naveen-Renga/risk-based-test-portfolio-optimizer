import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import './Sidebar.css';

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/assessment', label: 'Student Assessment', icon: '📝', roles: ['student', 'admin'] },
  { path: '/test-cases', label: 'Test Cases', icon: '🧪', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/defect-history', label: 'Defect History', icon: '🐛', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/risk-analysis', label: 'Risk Analysis', icon: '⚠️', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/portfolio', label: 'Portfolio Optimizer', icon: '🎯', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/experiments', label: 'Experiment Results', icon: '📈', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/events', label: 'Event Simulation', icon: '⚡', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/security', label: 'Security / Access', icon: '🔒', roles: ['tester', 'test_lead', 'admin'] },
  { path: '/workflow', label: 'Workflow Map', icon: '🗺️', roles: ['student', 'tester', 'test_lead', 'admin'] },
];

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const filtered = navItems.filter(item => user && item.roles.includes(user.role));

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="sidebar-logo">🎯</div>
        <h2>TestOptimizer</h2>
        <span className="sidebar-version">v1.0</span>
      </div>

      <nav className="sidebar-nav">
        {filtered.map(item => (
          <NavLink key={item.path} to={item.path} className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <div className="sidebar-footer">
        <div className="user-info">
          <div className="user-avatar">{user?.full_name?.charAt(0) || '?'}</div>
          <div className="user-details">
            <span className="user-name">{user?.full_name}</span>
            <span className="user-role">{user?.role?.replace('_', ' ').toUpperCase()}</span>
          </div>
        </div>
        <button className="logout-btn" onClick={handleLogout}>↗ Logout</button>
      </div>
    </aside>
  );
}
