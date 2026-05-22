const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
    ...options,
  });
  if (!res.ok) {
    const message = await res.text();
    throw new Error(message || `Error HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  health: () => request('/health'),
  modules: () => request('/api/modules'),
  module: (id) => request(`/api/modules/${id}`),
  dashboard: (userId = 'ana') => request(`/api/students/${userId}/dashboard`),
  saveCheckpoint: (moduleId, data) => request(`/api/modules/${moduleId}/checkpoints`, { method: 'POST', body: JSON.stringify(data) }),
  saveSurvey: (moduleId, data) => request(`/api/modules/${moduleId}/surveys`, { method: 'POST', body: JSON.stringify(data) }),
  scenarioAction: (data) => request('/api/scenarios/action', { method: 'POST', body: JSON.stringify(data) }),
  analytics: () => request('/api/teacher/analytics'),
};
