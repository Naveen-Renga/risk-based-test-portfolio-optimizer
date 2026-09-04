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

  // Assessments
  getAssessments: () => request('/assessments/'),
  getAssessment: (id: number) => request(`/assessments/${id}`),
  getQuestions: (id: number) => request(`/assessments/${id}/questions`),
  startAssessment: (userId: number, assessmentId: number) =>
    request('/assessments/start', { method: 'POST', body: JSON.stringify({ user_id: userId, assessment_id: assessmentId }) }),
  saveAnswer: (submissionId: number, questionId: number, answer: string, token: string) =>
    request('/assessments/save-answer', { method: 'POST', body: JSON.stringify({ submission_id: submissionId, question_id: questionId, answer, token }) }),
  submitAssessment: (submissionId: number) =>
    request('/assessments/submit', { method: 'POST', body: JSON.stringify({ submission_id: submissionId }) }),
  getSubmission: (id: number) => request(`/assessments/submission/${id}`),
  getUserSubmissions: (userId: number) => request(`/assessments/user/${userId}/submissions`),

  // Test Cases
  getTestCases: () => request('/test-cases/'),
  getDefectHistory: () => request('/test-cases/defects/history'),
  getDefectSummary: () => request('/test-cases/defects/summary'),

  // Risk
  getRiskScores: () => request('/risk/scores'),
  getRiskWeights: () => request('/risk/weights'),
  getRiskDistribution: () => request('/risk/distribution'),
  getRiskFormula: () => request('/risk/formula'),

  // Optimizer
  runOptimizer: (params: any) =>
    request('/optimizer/run', { method: 'POST', body: JSON.stringify(params) }),
  override: (data: any) =>
    request('/optimizer/override', { method: 'POST', body: JSON.stringify(data) }),
  getOverrides: () => request('/optimizer/overrides'),

  // Events
  simulateEvents: (data: any) =>
    request('/events/simulate', { method: 'POST', body: JSON.stringify(data) }),
  simulateDuplicate: () => request('/events/simulate/duplicate', { method: 'POST' }),
  simulateDelayed: () => request('/events/simulate/delayed', { method: 'POST' }),
  simulateOutOfOrder: () => request('/events/simulate/out-of-order', { method: 'POST' }),
  getEventLogs: () => request('/events/logs'),

  // Experiments
  runExperiment: (timeBudget: number) =>
    request('/experiments/run', { method: 'POST', body: JSON.stringify({ time_budget_minutes: timeBudget }) }),

  // Security
  securityCheck: (token: string, action: string) =>
    request('/security/check', { method: 'POST', body: JSON.stringify({ token, action }) }),
  securityDemo: () => request('/security/demo', { method: 'POST' }),
  getSecurityLogs: () => request('/security/logs'),
  getPermissions: () => request('/security/permissions'),
};
