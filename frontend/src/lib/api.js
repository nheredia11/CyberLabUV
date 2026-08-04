const API_BASE =
  import.meta.env.VITE_API_BASE_URL ||
  import.meta.env.VITE_API_URL ||
  "http://127.0.0.1:8000";

const DEV_TOKEN =
  import.meta.env.VITE_CYBERLAB_TOKEN ||
  "cyberlabuv-local-token";

function buildQuery(params = {}) {
  const search = new URLSearchParams();

  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      search.set(key, value);
    }
  });

  const query = search.toString();
  return query ? `?${query}` : "";
}

function getHeaders({ json = true } = {}) {
  const headers = {
    Accept: "application/json",
    "X-CyberLab-Token": DEV_TOKEN,
  };

  if (json) {
    headers["Content-Type"] = "application/json";
  }

  const sessionToken =
  localStorage.getItem("cyberlab_session_token") ||
  localStorage.getItem("cyberlab_token") ||
  localStorage.getItem("auth_token");

  if (sessionToken) {
    headers.Authorization = `Bearer ${sessionToken}`;
  }

  return headers;
}

async function parseResponse(response) {
  const contentType = response.headers.get("content-type") || "";
  const rawText = await response.text();

  if (!rawText) {
    return null;
  }

  if (contentType.includes("application/json")) {
    try {
      return JSON.parse(rawText);
    } catch {
      return rawText;
    }
  }

  try {
    return JSON.parse(rawText);
  } catch {
    return rawText;
  }
}

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...getHeaders({ json: options.body !== undefined }),
      ...(options.headers || {}),
    },
  });

  const data = await parseResponse(response);

  if (!response.ok) {
    const message =
      typeof data === "string"
        ? data
        : data?.detail || data?.message || `Error HTTP ${response.status}`;

    const error = new Error(message);
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

async function requestWithFallback(requests) {
  let lastError = null;

  for (const item of requests) {
    try {
      return await request(item.path, item.options || {});
    } catch (error) {
      lastError = error;

      if (![404, 405, 422].includes(error.status)) {
        throw error;
      }
    }
  }

  throw lastError || new Error("No fue posible completar la solicitud.");
}

function normalizeUserId(userId) {
  return userId || "demo-student";
}

function normalizeCheckpointPayload(moduleId, payload = {}) {
  const userId = normalizeUserId(payload.user_id || payload.student_id);

  return {
    user_id: userId,
    student_id: userId,
    module_id: payload.module_id || moduleId,
    checkpoint_id: payload.checkpoint_id,
    evidence: payload.evidence || "",
    status: payload.status || (payload.completed ? "completed" : "pending"),
    completed:
      payload.completed !== undefined
        ? payload.completed
        : (payload.status || "completed") === "completed",
  };
}

function normalizeSurveyPayload(moduleId, payload = {}) {
  const userId = normalizeUserId(payload.user_id || payload.student_id);

  return {
    user_id: userId,
    student_id: userId,
    module_id: payload.module_id || moduleId,
    answers: payload.answers || {},
    answers_json: payload.answers || {},
    rating: payload.rating || null,
    comments: payload.comments || "",
  };
}

export function getApiBase() {
  return API_BASE;
}

export function health() {
  return request("/health", {
    method: "GET",
  });
}

export function loginDemo({ email, role = "student", name = "" }) {
  return request("/api/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, role, name }),
  });
}

export function loginWithGoogle(credential) {
  return request("/api/auth/google", {
    method: "POST",
    body: JSON.stringify({ credential }),
  });
}

export function getUsers(role = "") {
  return request(`/api/users${buildQuery({ role })}`, {
    method: "GET",
  });
}

export function getModules() {
  return request("/api/modules", {
    method: "GET",
  });
}

export function getModuleById(moduleId, userId) {
  return request(`/api/modules/${moduleId}${buildQuery({ user_id: userId })}`, {
    method: "GET",
  });
}

export function getModule(moduleId, userId) {
  return getModuleById(moduleId, userId);
}

export function getModuleFeedback(moduleId, userId) {
  return request(
    `/api/modules/${moduleId}/feedback${buildQuery({ user_id: userId })}`,
    {
      method: "GET",
    }
  );
}

export function getStudentDashboard(userId) {
  return request(`/api/students/${userId}/dashboard`, {
    method: "GET",
  });
}

export function submitCheckpoint(moduleId, payload) {
  const body = normalizeCheckpointPayload(moduleId, payload);

  return requestWithFallback([
    {
      path: `/api/modules/${moduleId}/checkpoints`,
      options: {
        method: "POST",
        body: JSON.stringify(body),
      },
    },
    {
      path: "/api/progress/checkpoints",
      options: {
        method: "POST",
        body: JSON.stringify(body),
      },
    },
  ]);
}

export function submitSurvey(moduleId, payload) {
  const body = normalizeSurveyPayload(moduleId, payload);

  return requestWithFallback([
    {
      path: `/api/modules/${moduleId}/surveys`,
      options: {
        method: "POST",
        body: JSON.stringify(body),
      },
    },
    {
      path: "/api/surveys/responses",
      options: {
        method: "POST",
        body: JSON.stringify(body),
      },
    },
  ]);
}

export function runScenarioAction(payload) {
  const userId = normalizeUserId(payload.user_id || payload.student_id);
  const scenarioId = payload.scenario_id || payload.module_id;
  const action = payload.action;

  const originalBody = {
    user_id: userId,
    scenario_id: scenarioId,
    action,
  };

  const localAction = action === "reset" ? "restart" : action;

  return requestWithFallback([
    {
      path: "/api/scenarios/action",
      options: {
        method: "POST",
        body: JSON.stringify(originalBody),
      },
    },
    {
      path: `/api/scenarios/${scenarioId}/${localAction}`,
      options: {
        method: "POST",
      },
    },
  ]);
}

export function scenarioAction(payload) {
  return runScenarioAction(payload);
}

export async function runTerminalCommand({ user_id, scenario_id, command }) {
  const token = getStoredToken();
  const response = await fetch(
    `${API_URL}/api/scenarios/${encodeURIComponent(scenario_id)}/command`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "x-cyberlab-token": token,
      },
      body: JSON.stringify({ user_id, scenario_id, command }),
    }
  );

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(
      errorData.detail || "No fue posible ejecutar el comando en el escenario."
    );
  }

  return response.json();
}

export function terminalCommand(payload) {
  return runTerminalCommand(payload);
}

export function getTeacherAnalytics() {
  return request("/api/teacher/analytics", {
    method: "GET",
  });
}

export function createTeacherNote(payload) {
  return request("/api/teacher/notes", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function dashboard(userId) {
  return getStudentDashboard(userId);
}

export function modules() {
  return getModules();
}

export function moduleDetail(moduleId, userId) {
  return getModuleById(moduleId, userId);
}

export function feedback(moduleId, userId) {
  return getModuleFeedback(moduleId, userId);
}

export function checkpoint(moduleId, payload) {
  return submitCheckpoint(moduleId, payload);
}

export function survey(moduleId, payload) {
  return submitSurvey(moduleId, payload);
}

export function teacherAnalytics() {
  return getTeacherAnalytics();
}

const api = {
  getApiBase,
  health,

  loginDemo,
  loginWithGoogle,

  getUsers,
  getModules,
  getModuleById,
  getModule,
  getModuleFeedback,
  getStudentDashboard,

  submitCheckpoint,
  submitSurvey,

  runScenarioAction,
  scenarioAction,
  runTerminalCommand,
  terminalCommand,

  getTeacherAnalytics,
  createTeacherNote,

  // Compatibilidad con nombres anteriores usados en App.jsx y otras páginas
  dashboard,
  modules,
  module: moduleDetail,
  moduleDetail,
  feedback,
  checkpoint,
  survey,
  teacherAnalytics,
};

export { api };
export default api;