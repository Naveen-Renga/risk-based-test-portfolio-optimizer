import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../AuthContext';
import { api } from '../api';

export default function Login() {
  const [username, setUsername] = useState('tester1');
  const [password, setPassword] = useState('tester123');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const { login } = useAuth();
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await api.login(username, password);
      login(data);
      if (data.role === 'student') {
        navigate('/assessment');
      } else {
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.message || 'Login failed. Check credentials.');
    } finally {
      setLoading(false);
    }
  };

  const quickLogin = (u: string, p: string) => {
    setUsername(u);
    setPassword(p);
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ textAlign: 'center', fontSize: '40px', marginBottom: '8px' }}>🎯</div>
        <h1 className="login-title">Test Portfolio Optimizer</h1>
        <p className="login-subtitle">Risk-Based Portfolio Optimizer for Assessment Platform</p>

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Username</label>
            <input
              type="text"
              className="form-input"
              value={username}
              onChange={e => setUsername(e.target.value)}
              required
            />
          </div>

          <div className="form-group">
            <label className="form-label">Password</label>
            <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
              <input
                type={showPassword ? 'text' : 'password'}
                className="form-input"
                style={{ paddingRight: '45px', width: '100%' }}
                value={password}
                onChange={e => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '12px',
                  background: 'none',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '16px',
                  color: '#64748b',
                  userSelect: 'none',
                  padding: '4px'
                }}
                title={showPassword ? 'Hide Password' : 'Show Password'}
              >
                {showPassword ? '👁️' : '🙈'}
              </button>
            </div>
          </div>

          {error && <div className="login-error">{error}</div>}

          <button type="submit" className="login-btn" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign In'}
          </button>
        </form>

        <div className="login-hint">
          <h4>Demo Credentials (Role-Based Access)</h4>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginTop: '8px' }}>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => quickLogin('student1', 'student123')}
            >
              🎓 Student
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => quickLogin('tester1', 'tester123')}
            >
              🧪 Tester
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => quickLogin('testlead', 'lead123')}
            >
              👑 Test Lead
            </button>
            <button
              type="button"
              className="btn btn-secondary btn-sm"
              onClick={() => quickLogin('admin', 'admin123')}
            >
              ⚡ Admin
            </button>
          </div>
          <p style={{ fontSize: '11px', marginTop: '10px', textAlign: 'center', color: '#64748b' }}>
            Passwords: <code>student123</code> / <code>tester123</code> / <code>lead123</code> / <code>admin123</code>
          </p>
        </div>
      </div>
    </div>
  );
}
