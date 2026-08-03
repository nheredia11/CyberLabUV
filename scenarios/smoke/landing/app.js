const DEFAULT_API_BASE = 'http://127.0.0.1:8000';
const DEFAULT_TOKEN = 'cyberlabuv-local-token';
const DEFAULT_STUDENT = 'nestor';

const SCENARIO_URLS = {
  S01: 'http://127.0.0.1:8083',
  S02: 'http://127.0.0.1:8081',
  S03: 'http://127.0.0.1:8084',
  S04: 'http://127.0.0.1:8085',
  S05: 'http://127.0.0.1:8086'
};

let catalog = [];
let currentModuleId = localStorage.getItem('cyberlab_current_module') || 'S02';
let currentModule = null;
let currentProgress = null;

function getConfig() {
  return {
    apiBase: localStorage.getItem('cyberlab_api_base') || DEFAULT_API_BASE,
    token: localStorage.getItem('cyberlab_token') || DEFAULT_TOKEN,
    studentId: localStorage.getItem('cyberlab_student_id') || DEFAULT_STUDENT
  };
}

function setConfigFields() {
  const config = getConfig();

  document.getElementById('api-base').value = config.apiBase;
  document.getElementById('api-token').value = config.token;
  document.getElementById('student-id').value = config.studentId;
}

function saveConfig() {
  localStorage.setItem('cyberlab_api_base', document.getElementById('api-base').value.trim());
  localStorage.setItem('cyberlab_token', document.getElementById('api-token').value.trim());
  localStorage.setItem('cyberlab_student_id', document.getElementById('student-id').value.trim());
  localStorage.setItem('cyberlab_current_module', document.getElementById('module-select').value);

  currentModuleId = document.getElementById('module-select').value;
  refreshAll();
}

function apiHeaders(json = false) {
  const config = getConfig();
  const headers = { 'X-CyberLab-Token': config.token };

  if (json) {
    headers['Content-Type'] = 'application/json';
  }

  return headers;
}

async function apiGet(path, protectedRoute = false) {
  const config = getConfig();

  const options = protectedRoute
    ? { headers: apiHeaders(false) }
    : {};

  const response = await fetch(`${config.apiBase}${path}`, options);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }

  return response.json();
}

async function apiPost(path, body = null) {
  const config = getConfig();

  const options = {
    method: 'POST',
    headers: apiHeaders(Boolean(body))
  };

  if (body) {
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${config.apiBase}${path}`, options);

  if (!response.ok) {
    const text = await response.text();
    throw new Error(`${response.status} ${response.statusText}: ${text}`);
  }

  return response.json();
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function markdownToHtml(markdown) {
  const lines = String(markdown || '').split('\n');
  let html = '';
  let inList = false;

  for (const rawLine of lines) {
    const line = rawLine.trim();

    if (!line) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      continue;
    }

    if (line.startsWith('# ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h1>${escapeHtml(line.slice(2))}</h1>`;
      continue;
    }

    if (line.startsWith('## ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h2>${escapeHtml(line.slice(3))}</h2>`;
      continue;
    }

    if (line.startsWith('### ')) {
      if (inList) {
        html += '</ul>';
        inList = false;
      }
      html += `<h3>${escapeHtml(line.slice(4))}</h3>`;
      continue;
    }

    if (line.startsWith('- ')) {
      if (!inList) {
        html += '<ul>';
        inList = true;
      }

      html += `<li>${escapeHtml(line.slice(2))}</li>`;
      continue;
    }

    if (inList) {
      html += '</ul>';
      inList = false;
    }

    html += `<p>${escapeHtml(line)}</p>`;
  }

  if (inList) {
    html += '</ul>';
  }

  return html;
}

function setText(id, value) {
  const element = document.getElementById(id);
  if (element) {
    element.textContent = value;
  }
}

function prettyJson(value) {
  return JSON.stringify(value, null, 2);
}

function getLabUrl(moduleId = currentModuleId) {
  return SCENARIO_URLS[moduleId] || null;
}

function formatDate(value) {
  if (!value) return 'Sin fecha';

  try {
    return new Date(value).toLocaleString('es-CO');
  } catch {
    return value;
  }
}

function updateLabLink() {
  const labUrl = getLabUrl();
  const link = document.getElementById('current-lab-link');

  setText('current-lab-url', labUrl || 'No aplica');

  if (labUrl) {
    link.href = labUrl;
    link.textContent = `Abrir laboratorio ${currentModuleId}`;
    link.classList.remove('disabled');
  } else {
    link.href = '#';
    link.textContent = 'Módulo sin laboratorio';
  }
}

function updateScenarioButtons() {
  const hasScenario = Boolean(getLabUrl());

  document.querySelectorAll('[data-scenario-action]').forEach(button => {
    button.disabled = !hasScenario;
  });

  document.getElementById('btn-check-lab').disabled = !hasScenario;
}

async function loadBackendHealth() {
  try {
    const data = await apiGet('/health');

    setText('metric-backend', 'Activo');
    setText('metric-backend-detail', `${data.project} · ${data.environment}`);

    return data;
  } catch (error) {
    setText('metric-backend', 'Error');
    setText('metric-backend-detail', 'Backend no disponible');
    return null;
  }
}

async function loadLabHealth() {
  const labUrl = getLabUrl();

  if (!labUrl) {
    setText('metric-lab', 'No aplica');
    setText('metric-lab-detail', 'Módulo sin contenedor Docker');
    return null;
  }

  try {
    const response = await fetch(`${labUrl}/health`);

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const data = await response.json();

    setText('metric-lab', 'Activo');
    setText('metric-lab-detail', `${data.scenario_id || currentModuleId} · ${data.mode || 'lab'} · eventos: ${data.events ?? data.attempts ?? 0}`);

    return data;
  } catch (error) {
    setText('metric-lab', 'Inactivo');
    setText('metric-lab-detail', `Ejecuta Iniciar ${currentModuleId}`);
    return null;
  }
}

async function loadModules() {
  const select = document.getElementById('module-select');

  try {
    catalog = await apiGet('/api/modules');

    if (!catalog.find(item => item.id === currentModuleId)) {
      currentModuleId = catalog.find(item => item.id !== 'M00')?.id || 'M00';
      localStorage.setItem('cyberlab_current_module', currentModuleId);
    }

    select.innerHTML = catalog.map(item => `
      <option value="${escapeHtml(item.id)}" ${item.id === currentModuleId ? 'selected' : ''}>
        ${escapeHtml(item.id)} · ${escapeHtml(item.titulo)}
      </option>
    `).join('');

    renderCatalog();
  } catch (error) {
    document.getElementById('scenario-grid').innerHTML = `
      <article class="card tile">
        <h3>No fue posible cargar el catálogo</h3>
        <p class="bad-text">${escapeHtml(error.message)}</p>
      </article>
    `;
  }
}

function renderCatalog() {
  const container = document.getElementById('scenario-grid');

  container.innerHTML = catalog.map(item => {
    const isConfigured = item.estado.toLowerCase().includes('config')
      || item.estado.toLowerCase().includes('operativo');

    const isActive = item.id === currentModuleId;

    return `
      <article class="card tile catalog-card ${isActive ? 'active' : ''}" data-catalog-id="${escapeHtml(item.id)}">
        <div class="status">
          <span class="dot ${isConfigured ? '' : 'warn'}"></span>
          ${escapeHtml(item.estado)}
        </div>

        <h3>${escapeHtml(item.id)} · ${escapeHtml(item.titulo)}</h3>

        <div class="tag-row">
          <span class="tag">${escapeHtml(item.nivel)}</span>
          <span class="tag">${escapeHtml(item.duracion_estimada || 'Sin duración')}</span>
          ${SCENARIO_URLS[item.id] ? `<span class="tag">${escapeHtml(SCENARIO_URLS[item.id])}</span>` : '<span class="tag">Sin contenedor</span>'}
        </div>

        <p>Tipo: ${escapeHtml(item.tipo)}</p>
        <p>Ruta: <code>${escapeHtml(item.ruta)}</code></p>
      </article>
    `;
  }).join('');

  document.querySelectorAll('[data-catalog-id]').forEach(card => {
    card.addEventListener('click', () => selectModule(card.dataset.catalogId));
  });
}

async function selectModule(moduleId) {
  currentModuleId = moduleId;
  localStorage.setItem('cyberlab_current_module', moduleId);

  const select = document.getElementById('module-select');
  select.value = moduleId;

  updateLabLink();
  updateScenarioButtons();
  renderCatalog();

  await loadCurrentModule();
  await loadModuleProgress();
  await loadLabHealth();
}

async function loadCurrentModule() {
  const summary = document.getElementById('module-summary');
  const theory = document.getElementById('module-theory');

  try {
    currentModule = await apiGet(`/api/modules/${encodeURIComponent(currentModuleId)}`);

    setText('module-heading', `${currentModule.id} · ${currentModule.titulo}`);
    setText('selected-scenario-title', `${currentModule.id} · ${currentModule.titulo}`);
    setText('selected-scenario-description', currentModule.descripcion);

    const tags = document.getElementById('selected-scenario-tags');
    tags.innerHTML = `
      <span class="tag">${escapeHtml(currentModule.catalog?.nivel || 'Sin nivel')}</span>
      <span class="tag">${escapeHtml(currentModule.catalog?.duracion_estimada || 'Sin duración')}</span>
      ${(currentModule.catalog?.frameworks || []).map(item => `<span class="tag">${escapeHtml(item)}</span>`).join('')}
    `;

    summary.innerHTML = `
      <p><strong>ID:</strong> ${escapeHtml(currentModule.id)}</p>
      <p><strong>Título:</strong> ${escapeHtml(currentModule.titulo)}</p>
      <p><strong>Descripción:</strong> ${escapeHtml(currentModule.descripcion)}</p>
      <p><strong>Comando:</strong> <code>${escapeHtml(currentModule.comando_inicio || 'No aplica')}</code></p>

      ${!getLabUrl() ? `
        <div class="disabled-note">
          Este módulo corresponde a contenido fundacional y no requiere contenedor Docker.
        </div>
      ` : ''}

      <h4>Objetivos</h4>
      <ul>
        ${currentModule.objetivos.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
      </ul>
    `;

    theory.innerHTML = markdownToHtml(currentModule.theory_markdown);

    renderCheckpoints(currentModule.checkpoints);
    renderSurvey(currentModule.survey);
  } catch (error) {
    summary.innerHTML = `<p class="bad-text">${escapeHtml(error.message)}</p>`;
    theory.innerHTML = '<p>No fue posible cargar la teoría.</p>';
  }
}

function getProgressRecord(checkpointId) {
  if (!currentProgress || !currentProgress.checkpoints) {
    return null;
  }

  return currentProgress.checkpoints.find(item => item.checkpoint_id === checkpointId) || null;
}

async function loadModuleProgress() {
  const config = getConfig();

  try {
    currentProgress = await apiGet(
      `/api/students/${encodeURIComponent(config.studentId)}/modules/${encodeURIComponent(currentModuleId)}/progress`,
      true
    );

    setText('metric-progress', `${currentProgress.checkpoints_completed} / ${currentProgress.checkpoints_total}`);
    setText('metric-progress-detail', `${currentModuleId} · checkpoints del módulo`);
    setText('metric-percent', `${currentProgress.progress_percent}%`);

    if (currentModule) {
      renderCheckpoints(currentModule.checkpoints);
    }

    return currentProgress;
  } catch (error) {
    currentProgress = null;
    setText('metric-progress', '0 / 0');
    setText('metric-progress-detail', 'Sin progreso del módulo');
    setText('metric-percent', '0%');
    return null;
  }
}

function defaultEvidence(checkpointId, index) {
  const defaults = {
    'm00-cp1': 'Se leyeron y aceptaron las reglas de uso académico, ético y controlado del simulador.',
    'm00-cp2': 'Se identificaron los componentes principales: plataforma web, backend, Docker y escenarios de laboratorio.',
    'm00-cp3': 'El estudiante confirma que comprende los límites del simulador y su uso únicamente académico.',

    's01-cp1': 'El laboratorio S01 está disponible en http://127.0.0.1:8083 y responde correctamente en /health.',
    's01-cp2': 'Se observaron servicios HTTP y servicios simulados tipo SSH/FTP dentro del entorno de laboratorio.',
    's01-cp3': 'Se registraron puertos, banners o eventos visibles en el laboratorio de reconocimiento.',
    's01-cp4': 'Se proponen controles como cerrar servicios innecesarios, segmentar red y monitorear exposición.',

    's02-cp1': 'Se accedió correctamente al laboratorio S02 en http://127.0.0.1:8081 y se verificó el endpoint /health con estado ok.',
    's02-cp2': 'Se observaron intentos repetidos sin bloqueo progresivo y credenciales de laboratorio simples.',
    's02-cp3': 'El sistema registra intentos válidos y fallidos en la interfaz y permite consultar /attempts.',
    's02-cp4': 'Se proponen bloqueo progresivo, MFA, contraseñas robustas y monitoreo de intentos fallidos.',

    's03-cp1': 'El laboratorio S03 está disponible en http://127.0.0.1:8084 y responde correctamente en /health.',
    's03-cp2': 'Se observó el comportamiento del formulario de búsqueda ante entradas de usuario.',
    's03-cp3': 'Se analizó el riesgo de entradas no sanitizadas en comentarios.',
    's03-cp4': 'Se revisó el comportamiento de solicitud de archivos dentro del laboratorio.',
    's03-cp5': 'Se proponen validación de entradas, sanitización, autorización y manejo seguro de errores.',

    's04-cp1': 'El laboratorio S04 está disponible en http://127.0.0.1:8085 y responde correctamente en /health.',
    's04-cp2': 'Se registraron intentos fallidos de autenticación simulada y se observaron en eventos.',
    's04-cp3': 'Se registró un intento válido usando las credenciales de laboratorio.',
    's04-cp4': 'Se proponen bloqueo progresivo, MFA, llaves SSH, registros centralizados y alertas.',

    's05-cp1': 'El laboratorio S05 está disponible en http://127.0.0.1:8086 y responde correctamente en /health.',
    's05-cp2': 'Se envió un mensaje de laboratorio sin datos sensibles para observar el flujo simulado.',
    's05-cp3': 'Se observó el evento registrado en la tabla del laboratorio.',
    's05-cp4': 'Se proponen HTTPS/TLS, validación de certificados, segmentación y monitoreo de tráfico anómalo.'
  };

  return defaults[checkpointId] || `Evidencia del checkpoint ${index + 1}.`;
}

function renderCheckpoints(checkpoints) {
  const container = document.getElementById('checkpoint-list');

  if (!checkpoints || checkpoints.length === 0) {
    container.innerHTML = '<p>No hay checkpoints definidos.</p>';
    return;
  }

  container.innerHTML = checkpoints.map((checkpoint, index) => {
    const progressRecord = getProgressRecord(checkpoint.id);
    const isCompleted = Boolean(progressRecord && progressRecord.completed);
    const savedEvidence = progressRecord ? progressRecord.evidence : '';
    const evidenceValue = savedEvidence || defaultEvidence(checkpoint.id, index);

    return `
      <article class="checkpoint-card ${isCompleted ? 'completed' : ''}">
        <div class="checkpoint-status ${isCompleted ? 'completed' : ''}">
          <span class="dot ${isCompleted ? '' : 'warn'}"></span>
          ${isCompleted ? 'Checkpoint completado' : 'Checkpoint pendiente'}
        </div>

        <h3>${escapeHtml(checkpoint.titulo)}</h3>
        <p><strong>ID:</strong> <code>${escapeHtml(checkpoint.id)}</code></p>
        <p><strong>Evidencia esperada:</strong> ${escapeHtml(checkpoint.evidencia)}</p>

        ${savedEvidence ? `
          <div class="saved-evidence">
            <strong>Evidencia guardada</strong>
            <p>${escapeHtml(savedEvidence)}</p>
            <div class="checkpoint-date">
              Última actualización: ${escapeHtml(formatDate(progressRecord.updated_at))}
            </div>
          </div>
        ` : ''}

        <label>
          Evidencia registrada
          <textarea id="evidence-${escapeHtml(checkpoint.id)}">${escapeHtml(evidenceValue)}</textarea>
        </label>

        <div class="checkpoint-actions">
          <small>Tipo: ${escapeHtml(checkpoint.tipo)}</small>
          <button class="btn" data-checkpoint-id="${escapeHtml(checkpoint.id)}">
            ${isCompleted ? 'Actualizar evidencia' : 'Guardar checkpoint'}
          </button>
        </div>
      </article>
    `;
  }).join('');

  document.querySelectorAll('[data-checkpoint-id]').forEach(button => {
    button.addEventListener('click', () => submitCheckpoint(button.dataset.checkpointId));
  });
}

async function submitCheckpoint(checkpointId) {
  if (!currentModule) return;

  const config = getConfig();
  const evidence = document.getElementById(`evidence-${checkpointId}`).value.trim();

  const body = {
    student_id: config.studentId,
    module_id: currentModule.id,
    checkpoint_id: checkpointId,
    evidence,
    completed: true
  };

  try {
    const data = await apiPost('/api/progress/checkpoints', body);
    setText('scenario-output', prettyJson(data));
    await loadDashboards();
    await loadModuleProgress();
  } catch (error) {
    setText('scenario-output', error.message);
  }
}

function renderSurvey(questions) {
  const container = document.getElementById('survey-form');

  if (!questions || questions.length === 0) {
    container.innerHTML = '<p>No hay encuesta definida.</p>';
    return;
  }

  container.innerHTML = `
    <div class="grid-2">
      ${questions.map(question => `
        <label>
          ${escapeHtml(question.pregunta)}
          ${question.tipo === 'likert_1_5'
            ? `
              <select id="survey-${escapeHtml(question.id)}">
                <option value="5">5 - Totalmente de acuerdo</option>
                <option value="4">4 - De acuerdo</option>
                <option value="3">3 - Neutral</option>
                <option value="2">2 - En desacuerdo</option>
                <option value="1">1 - Totalmente en desacuerdo</option>
              </select>
            `
            : `<textarea id="survey-${escapeHtml(question.id)}">Agregaría primero un control preventivo y monitoreo de eventos.</textarea>`
          }
        </label>
      `).join('')}
    </div>

    <button class="btn full" id="btn-submit-survey">Guardar encuesta de ${escapeHtml(currentModuleId)}</button>
  `;

  document.getElementById('btn-submit-survey').addEventListener('click', submitSurvey);
}

async function submitSurvey() {
  if (!currentModule) return;

  const config = getConfig();
  const answers = {};

  currentModule.survey.forEach(question => {
    const element = document.getElementById(`survey-${question.id}`);
    const rawValue = element.value;

    answers[question.id] = question.tipo === 'likert_1_5'
      ? Number(rawValue)
      : rawValue;
  });

  const body = {
    student_id: config.studentId,
    module_id: currentModule.id,
    answers
  };

  try {
    const data = await apiPost('/api/surveys/responses', body);
    setText('scenario-output', prettyJson(data));
    await loadDashboards();
  } catch (error) {
    setText('scenario-output', error.message);
  }
}

async function scenarioAction(action) {
  if (!getLabUrl()) {
    setText('scenario-output', 'Este módulo no tiene escenario Docker asociado.');
    return;
  }

  try {
    setText('scenario-output', `Ejecutando acción ${action} para ${currentModuleId}...`);

    const data = await apiPost(`/api/scenarios/${encodeURIComponent(currentModuleId)}/${action}`);
    setText('scenario-output', prettyJson(data));

    await loadLabHealth();

    if (action === 'start' || action === 'restart') {
      setTimeout(loadLabHealth, 2500);
    }
  } catch (error) {
    setText('scenario-output', error.message);
  }
}

async function loadDashboards() {
  const config = getConfig();

  try {
    const dashboard = await apiGet(`/api/students/${encodeURIComponent(config.studentId)}/dashboard`, true);
    setText('student-dashboard', prettyJson(dashboard));
  } catch (error) {
    setText('student-dashboard', error.message);
  }

  try {
    const analytics = await apiGet('/api/teacher/analytics', true);
    setText('teacher-analytics', prettyJson(analytics));
  } catch (error) {
    setText('teacher-analytics', error.message);
  }
}

async function refreshAll() {
  updateLabLink();
  updateScenarioButtons();

  await loadBackendHealth();
  await loadModules();
  await loadCurrentModule();
  await loadModuleProgress();
  await loadLabHealth();
  await loadDashboards();
}

function bindEvents() {
  document.getElementById('btn-save-config').addEventListener('click', saveConfig);
  document.getElementById('btn-refresh-all').addEventListener('click', refreshAll);
  document.getElementById('btn-check-lab').addEventListener('click', loadLabHealth);

  document.getElementById('module-select').addEventListener('change', event => {
    selectModule(event.target.value);
  });

  document.querySelectorAll('[data-scenario-action]').forEach(button => {
    button.addEventListener('click', () => scenarioAction(button.dataset.scenarioAction));
  });
}

setConfigFields();
bindEvents();
refreshAll();