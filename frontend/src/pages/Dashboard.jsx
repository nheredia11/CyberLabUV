import {
  Activity,
  Award,
  BookOpen,
  CheckCircle2,
  Clock3,
  Flame,
  Lightbulb,
  PlayCircle,
  ShieldCheck,
  Star,
  Target,
  TrendingUp,
} from 'lucide-react';
import { Kpi, ProgressBar } from '../components/Cards.jsx';

function Ring({ value = 0, label = 'Progreso' }) {
  const safeValue = Math.max(0, Math.min(100, value));
  const deg = safeValue * 3.6;

  return (
    <div className="progress-ring-card">
      <div
        className="ring xl"
        style={{
          background: `conic-gradient(var(--accent) ${deg}deg, var(--border) 0deg)`,
        }}
      >
        <span>{safeValue}%</span>
      </div>
      <strong>{label}</strong>
      <small className="muted">Avance global de la ruta</small>
    </div>
  );
}

function ModuleStatus({ percent }) {
  if (percent >= 100) return <span className="status-pill done">Completado</span>;
  if (percent >= 60) return <span className="status-pill progress">En progreso</span>;
  if (percent > 0) return <span className="status-pill started">Iniciado</span>;
  return <span className="status-pill pending">Pendiente</span>;
}

function getRecommendedModule(modules = []) {
  return modules.find((module) => module.progress?.percent < 100) || modules[0];
}

export default function Dashboard({ data, user, setView, setSelectedModule }) {
  if (!data) {
    return (
      <div className="dashboard-loading card">
        <div className="loading-pulse" />
        <div>
          <h3>Cargando dashboard académico...</h3>
          <p className="muted">Estamos consultando tu progreso, checkpoints y retroalimentación.</p>
        </div>
      </div>
    );
  }

  const modules = data.modules || [];
  const recommended = getRecommendedModule(modules);
  const completedCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.completed_checkpoints || 0),
    0,
  );
  const totalCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.total_checkpoints || 0),
    0,
  );

  const pendingModules = modules.filter((module) => module.progress?.percent < 100).length;
  const strongModules = modules.filter((module) => module.progress?.percent >= 70).length;

  function openModule(moduleId) {
    setSelectedModule(moduleId);
    setView('route');
  }

  return (
    <div className="student-dashboard">
      <section className="student-hero">
        <div className="student-hero-content">
          <span className="badge">
            <ShieldCheck size={14} />
            CyberLab · acceso institucional
          </span>

          <h2>
            Hola, {user?.name?.split(' ')[0] || 'estudiante'}. Bienvenido a CyberLab.
          </h2>

          <p>
            Continúa con tu ruta de aprendizaje, ejecuta el escenario práctico,
            registra evidencias y revisa la retroalimentación generada a partir
            de tus checkpoints.
          </p>

          <div className="hero-actions">
            <button
              className="btn"
              onClick={() => openModule(recommended?.id || 'S02')}
            >
              <Target size={16} />
              Continuar módulo recomendado
            </button>

            <button
              className="btn secondary"
              onClick={() => setView('practice')}
            >
              <PlayCircle size={16} />
              Abrir laboratorio local
            </button>
          </div>
        </div>

        <Ring value={data.general_percent} label="Progreso general" />
      </section>

      <section className="dashboard-kpis">
        <Kpi
          icon={BookOpen}
          label="Módulos completados"
          value={`${data.completed_modules}/${data.total_modules}`}
        />

        <Kpi
          icon={CheckCircle2}
          label="Checkpoints logrados"
          value={`${completedCheckpoints}/${totalCheckpoints}`}
        />

        <Kpi
          icon={Flame}
          label="Puntos acumulados"
          value={data.points}
        />

        <Kpi
          icon={Award}
          label="Insignias"
          value={data.badges}
        />
      </section>

      <section className="dashboard-main-grid">
        <article className="card recommended-card">
          <div className="section-title">
            <div>
              <span className="badge">Siguiente paso</span>
              <h2>{recommended?.titulo || 'Ruta de aprendizaje'}</h2>
              <p className="muted">
                Este módulo fue seleccionado porque aún tiene actividades pendientes.
              </p>
            </div>
            <ModuleStatus percent={recommended?.progress?.percent || 0} />
          </div>

          <div className="recommended-progress">
            <div>
              <strong>{recommended?.progress?.percent || 0}%</strong>
              <span className="muted">avance del módulo</span>
            </div>
            <ProgressBar value={recommended?.progress?.percent || 0} />
          </div>

          <div className="feedback-highlight">
            <Lightbulb size={20} />
            <div>
              <strong>{recommended?.feedback?.level || 'Nivel pendiente'}</strong>
              <p className="muted">
                {recommended?.feedback?.message ||
                  'Completa los primeros pasos para recibir retroalimentación.'}
              </p>
            </div>
          </div>

          <div className="next-actions">
            {(recommended?.feedback?.next_actions || []).slice(0, 3).map((action) => (
              <div key={action} className="next-action">
                <CheckCircle2 size={16} />
                <span>{action}</span>
              </div>
            ))}
          </div>

          <button
            className="btn full"
            onClick={() => openModule(recommended?.id || 'S02')}
          >
            Ir al módulo
          </button>
        </article>

        <article className="card lab-status-card">
          <div className="section-title">
            <div>
              <span className="badge">Laboratorio</span>
              <h2>Estado de práctica</h2>
            </div>
            <Activity size={24} />
          </div>

          <div className="lab-status-list">
            <div>
              <strong>Terminal guiada</strong>
              <span className="status-pill done">Disponible</span>
            </div>

            <div>
              <strong>Escenario Docker</strong>
              <span className="status-pill progress">Listo para iniciar</span>
            </div>

            <div>
              <strong>Evidencias</strong>
              <span className="status-pill started">Registro activo</span>
            </div>
          </div>

          <div className="mini-terminal-preview">
            <div className="terminal-header">
              <span />
              <span />
              <span />
              <strong>cyberlabuv@lab</strong>
            </div>
            <pre>{`$ curl -i http://localhost:8082/login
HTTP/1.1 200 OK
Formulario de autenticación disponible.`}</pre>
          </div>

          <button
            className="btn secondary full"
            onClick={() => setView('practice')}
          >
            Ejecutar práctica
          </button>
        </article>
      </section>

      <section className="card">
        <div className="section-title">
          <div>
            <span className="badge">Ruta completa</span>
            <h2>Mapa de módulos</h2>
            <p className="muted">
              Visualiza tu avance por módulo y continúa desde el punto donde quedaste.
            </p>
          </div>

          <div className="route-summary">
            <div>
              <strong>{pendingModules}</strong>
              <span>Pendientes</span>
            </div>
            <div>
              <strong>{strongModules}</strong>
              <span>Con buen avance</span>
            </div>
          </div>
        </div>

        <div className="module-dashboard-list">
          {modules.map((module, index) => (
            <article className="module-dashboard-item" key={module.id}>
              <div className="module-index">
                {String(index + 1).padStart(2, '0')}
              </div>

              <div className="module-dashboard-body">
                <div className="module-row-title">
                  <div>
                    <strong>{module.titulo}</strong>
                    <p className="muted">{module.descripcion}</p>
                  </div>
                  <ModuleStatus percent={module.progress?.percent || 0} />
                </div>

                <ProgressBar value={module.progress?.percent || 0} />

                <div className="module-meta">
                  <span>
                    <CheckCircle2 size={14} />
                    {module.progress?.completed_checkpoints || 0}/
                    {module.progress?.total_checkpoints || 0} checkpoints
                  </span>
                  <span>
                    <TrendingUp size={14} />
                    {module.feedback?.level || 'Sin nivel'}
                  </span>
                  <span>
                    <Clock3 size={14} />
                    Encuesta: {module.progress?.survey_completed ? 'realizada' : 'pendiente'}
                  </span>
                </div>
              </div>

              <button
                className="btn ghost"
                onClick={() => openModule(module.id)}
              >
                <PlayCircle size={16} />
                Abrir
              </button>
            </article>
          ))}
        </div>
      </section>

      <section className="dashboard-bottom-grid">
        <article className="card insight-card">
          <span className="badge">Retroalimentación</span>
          <h3>Recomendación del sistema</h3>
          <p className="muted">
            Prioriza los checkpoints pendientes y registra evidencia mínima:
            comando ejecutado, resultado observado y explicación corta del hallazgo.
          </p>
        </article>

        <article className="card insight-card">
          <span className="badge">Validación pedagógica</span>
          <h3>Evidencias útiles para tu tesis</h3>
          <p className="muted">
            Este dashboard ya permite mostrar progreso, interacción con laboratorio,
            checkpoints y percepción del estudiante como datos de validación.
          </p>
        </article>

        <article className="card insight-card">
          <span className="badge">Objetivo académico</span>
          <h3>Aprendizaje aplicado</h3>
          <p className="muted">
            La plataforma conecta teoría, práctica y analítica para apoyar la enseñanza
            de ciberseguridad en un ambiente controlado.
          </p>
        </article>
      </section>
    </div>
  );
}