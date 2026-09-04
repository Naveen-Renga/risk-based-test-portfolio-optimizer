const API_BASE = 'http://localhost:8000/api';

async function request(url: string, options: RequestInit = {}) {
  const res = await fetch(`${API_BASE}${url}`, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'Request failed' }));
    throw new Error(err.detail || 'Request failed');
  }
  return res.json();
}

export const api = {
  // Auth
  login: (username: string, password: string) =>
    request('/auth/login', { method: 'POST', body: JSON.stringify({ username, password }) }),
  getUsers: (token: string) => request(`/auth/users?token=${encodeURIComponent(token)}`),

  // Dashboard
  getDashboardStats: () => request('/dashboard/stats'),

  // Assessments (Bug 7 Data Ownership)
  getAssessments: () => request('/assessments/'),
  getAssessment: (id: number) => request(`/assessments/${id}`),
  getQuestions: (id: number) => request(`/assessments/${id}/questions`),
  startAssessment: (userId: number, assessmentId: number, token: string) =>
    request('/assessments/start', { method: 'POST', body: JSON.stringify({ user_id: userId, assessment_id: assessmentId, token }) }),
  saveAnswer: (submissionId: number, questionId: number, answer: string, token: string) =>
    request('/assessments/save-answer', { method: 'POST', body: JSON.stringify({ submission_id: submissionId, question_id: questionId, answer, token }) }),
  submitAssessment: (submissionId: number, token: string) =>
    request('/assessments/submit', { method: 'POST', body: JSON.stringify({ submission_id: submissionId, token }) }),
  getSubmission: (id: number, token: string) => request(`/assessments/submission/${id}?token=${encodeURIComponent(token)}`),
  getUserSubmissions: (userId: number, token: string) => request(`/assessments/user/${userId}/submissions?token=${encodeURIComponent(token)}`),

  // Test Cases (Bug 3 RBAC)
  getTestCases: (token: string) => request(`/test-cases/?token=${encodeURIComponent(token)}`),
  getDefectHistory: (token: string) => request(`/test-cases/defects/history?token=${encodeURIComponent(token)}`),
  getDefectSummary: (token: string) => request(`/test-cases/defects/summary?token=${encodeURIComponent(token)}`),

  // Risk (Bug 3 RBAC)
  getRiskScores: (token: string) => request(`/risk/scores?token=${encodeURIComponent(token)}`),
  getRiskWeights: (token: string) => request(`/risk/weights?token=${encodeURIComponent(token)}`),
  getRiskDistribution: (token: string) => request(`/risk/distribution?token=${encodeURIComponent(token)}`),
  getRiskFormula: (token: string) => request(`/risk/formula?token=${encodeURIComponent(token)}`),

  // Optimizer (Bug 3 & 5 RBAC + Overrides)
  runOptimizer: (params: any) =>
    request('/optimizer/run', { method: 'POST', body: JSON.stringify(params) }),
  override: (data: any) =>
    request('/optimizer/override', { method: 'POST', body: JSON.stringify(data) }),
  getOverrides: (token: string) => request(`/optimizer/overrides?token=${encodeURIComponent(token)}`),

  // Events (Bug 3 RBAC)
  simulateEvents: (data: any) =>
    request('/events/simulate', { method: 'POST', body: JSON.stringify(data) }),
  simulateDuplicate: (token: string) => request(`/events/simulate/duplicate?token=${encodeURIComponent(token)}`, { method: 'POST' }),
  simulateDelayed: (token: string) => request(`/events/simulate/delayed?token=${encodeURIComponent(token)}`, { method: 'POST' }),
  simulateOutOfOrder: (token: string) => request(`/events/simulate/out-of-order?token=${encodeURIComponent(token)}`, { method: 'POST' }),
  getEventLogs: (token: string) => request(`/events/logs?token=${encodeURIComponent(token)}`),

  // Experiments (Bug 3 RBAC)
  runExperiment: (timeBudget: number, token: string) =>
    request('/experiments/run', { method: 'POST', body: JSON.stringify({ time_budget_minutes: timeBudget, token }) }),

  // Security (Bug 3 & 4)
  securityCheck: (token: string, action: string) =>
    request('/security/check', { method: 'POST', body: JSON.stringify({ token, action }) }),
  securityDemo: () => request('/security/demo', { method: 'POST' }),
  getSecurityLogs: (token: string) => request(`/security/logs?token=${encodeURIComponent(token)}`),
  getPermissions: () => request('/security/permissions'),
};
