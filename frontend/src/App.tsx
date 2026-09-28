import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './AuthContext';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import StudentAssessment from './pages/StudentAssessment';
import TestCases from './pages/TestCases';
import DefectHistory from './pages/DefectHistory';
import RiskAnalysis from './pages/RiskAnalysis';
import Portfolio from './pages/Portfolio';
import EventSimulation from './pages/EventSimulation';
import ExperimentResults from './pages/ExperimentResults';
import Security from './pages/Security';
import WorkflowMap from './pages/WorkflowMap';

function ProtectedLayout() {
  const { user } = useAuth();
  if (!user) return <Navigate to="/login" replace />;

  return (
    <div className="app-layout">
      <Sidebar />
      <main className="main-content">
        <Header />
        <Routes>
          <Route path="/dashboard" element={user.role === 'student' ? <Navigate to="/assessment" replace /> : <Dashboard />} />
          <Route path="/assessment" element={<StudentAssessment />} />
          <Route path="/test-cases" element={<TestCases />} />
          <Route path="/defect-history" element={<DefectHistory />} />
          <Route path="/risk-analysis" element={<RiskAnalysis />} />
          <Route path="/portfolio" element={<Portfolio />} />
          <Route path="/events" element={<EventSimulation />} />
          <Route path="/experiments" element={<ExperimentResults />} />
          <Route path="/security" element={<Security />} />
          <Route path="/workflow" element={<WorkflowMap />} />
          <Route path="*" element={<Navigate to={user.role === 'student' ? '/assessment' : '/dashboard'} replace />} />
        </Routes>
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/*" element={<ProtectedLayout />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
