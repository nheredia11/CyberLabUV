const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

async function request(path, options = {}) {
  const token = localStorage.getItem('cyberlab_token');

  const res = await fetch(`${API_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!res.ok) {
  let message = `Error HTTP ${res.status}`;

  try {
    const data = await res.json();
    message = data.detail || message;
  } catch {
    message = await res.text();
  }

  throw new Error(message);
  }

  return res.json();
}

export const api = {
  health: () => request('/health'),

  loginGoogle: (credential) =>
    request('/api/auth/google', {
      method: 'POST',
      body: JSON.stringify({ credential }),
    }),

  modules: () => request('/api/modules'),

  module: (id, userId = 'ana') =>
    request(`/api/modules/${id}?user_id=${userId}`),

  feedback: (moduleId, userId = 'ana') =>
    request(`/api/modules/${moduleId}/feedback?user_id=${userId}`),

  dashboard: (userId = 'ana') =>
    request(`/api/students/${userId}/dashboard`),

  saveCheckpoint: (moduleId, data) =>
    request(`/api/modules/${moduleId}/checkpoints`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  saveSurvey: (moduleId, data) =>
    request(`/api/modules/${moduleId}/surveys`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  scenarioAction: (data) =>
    request('/api/scenarios/action', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  terminal: (data) =>
    request('/api/scenarios/terminal', {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  analytics: () => request('/api/teacher/analytics'),
};