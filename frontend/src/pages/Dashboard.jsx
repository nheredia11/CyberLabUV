import { useMemo, useState } from 'react';
import {
  Activity,
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  Clock3,
  Flame,
  GraduationCap,
  Lightbulb,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Star,
  Target,
  TerminalSquare,
  TrendingUp,
  Trophy,
  Zap,
} from 'lucide-react';
import { Kpi, ProgressBar } from '../components/Cards.jsx';

function clamp(value = 0) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function getFirstName(name = '') {
  return name?.split(' ')?.[0] || 'estudiante';
}

function getRecommendedModule(modules = []) {
  return (
    modules.find((module) => module.progress?.percent > 0 && module.progress?.percent < 100) ||
    modules.find((module) => module.progress?.percent === 0) ||
    modules[0]
  );
}

function getStatus(percent = 0) {
  if (percent >= 100) {
    return {
      label: 'Completado',
      className: 'done',
    };
  }

  if (percent >= 60) {
    return {
      label: 'Avanzado',
      className: 'progress',
    };
  }

  if (percent > 0) {
    return {
      label: 'En progreso',
      className: 'started',
    };
  }

  return {
    label: 'Pendiente',
    className: 'pending',
  };
}

function StatusPill({ percent }) {
  const status = getStatus(percent);

  return (
    <span className={`status-pill ${status.className}`}>
      {status.label}
    </span>
  );
}

function ProgressRing({ value = 0, label = 'Progreso general' }) {
  const safeValue = clamp(value);
  const deg = safeValue * 3.6;

  return (
    <div className="student-progress-widget">
      <div
        className="student-progress-ring"
        style={{
          background: `conic-gradient(var(--accent) ${deg}deg, rgba(255,255,255,.18) 0deg)`,
        }}
      >
        <div>
          <strong>{safeValue}%</strong>
          <span>avance</span>
        </div>
      </div>

      <div>
        <strong>{label}</strong>
        <p>Ruta de formación práctica</p>
      </div>
    </div>
  );
}

function QuickAction({ icon: Icon, title, description, onClick, variant = 'primary' }) {
  return (
    <button className={`quick-action ${variant}`} onClick={onClick}>
      <span>
        <Icon size={20} />
      </span>

      <div>
        <strong>{title}</strong>
        <small>{description}</small>
      </div>

      <ChevronRight size={18} />
    </button>
  );
}

function Achievement({ icon: Icon, title, description, active }) {
  return (
    <div className={`achievement-card ${active ? 'active' : ''}`}>
      <span>
        <Icon size={20} />
      </span>

      <div>
        <strong>{title}</strong>
        <small>{description}</small>
      </div>
    </div>
  );
}

function ModuleCard({ module, index, onOpen }) {
  const percent = clamp(module.progress?.percent);
  const completed = module.progress?.completed_checkpoints || 0;
  const total = module.progress?.total_checkpoints || 0;

  return (
    <article className="student-module-card">
      <div className="module-card-header">
        <div className="module-number">
          {String(index + 1).padStart(2, '0')}
        </div>

        <StatusPill percent={percent} />
      </div>

      <h3>{module.titulo}</h3>

      <p>{module.descripcion}</p>

      <div className="module-card-progress">
        <div>
          <span>Avance</span>
          <strong>{percent}%</strong>
        </div>

        <ProgressBar value={percent} />
      </div>

      <div className="module-card-meta">
        <span>
          <CheckCircle2 size={14} />
          {completed}/{total} checkpoints
        </span>

        <span>
          <TrendingUp size={14} />
          {module.feedback?.level || 'Sin nivel'}
        </span>
      </div>

      <button className="btn ghost full" onClick={() => onOpen(module.id)}>
        Abrir módulo
        <ChevronRight size={16} />
      </button>
    </article>
  );
}

function TimelineStep({ number, title, description, active, done }) {
  return (
    <div className={`learning-step ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
      <span>{done ? <CheckCircle2 size={16} /> : number}</span>

      <div>
        <strong>{title}</strong>
        <small>{description}</small>
      </div>
    </div>
  );
}

export default function Dashboard({
  data,
  user,
  userId,
  setView,
  setSelectedModule,
  refreshDashboard,
}) {
  const [selectedTab, setSelectedTab] = useState('ruta');

  const modules = data?.modules || [];
  const recommended = useMemo(() => getRecommendedModule(modules), [modules]);

  const completedCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.completed_checkpoints || 0),
    0,
  );

  const totalCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.total_checkpoints || 0),
    0,
  );

  const pendingModules = modules.filter((module) => clamp(module.progress?.percent) < 100).length;
  const completedModules = data?.completed_modules || 0;
  const totalModules = data?.total_modules || modules.length || 0;
  const generalPercent = clamp(data?.general_percent);

  function openModule(moduleId) {
    setSelectedModule(moduleId);
    setView('route');
  }

  function openRecommended() {
    openModule(recommended?.id || 'S02');
  }

  if (!data) {
    return (
      <div className="student-dashboard">
        <section className="dashboard-skeleton">
          <div className="skeleton-icon" />
          <div>
            <h3>Cargando tu espacio de aprendizaje...</h3>
            <p>Estamos consultando tus módulos, progreso y recomendaciones.</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="student-dashboard pro">
      <section className="student-welcome-panel">
        <div className="welcome-main">
          <span className="welcome-badge">
            <ShieldCheck size={15} />
            CyberLab · sesión institucional activa
          </span>

          <h2>
            Hola, {getFirstName(user?.name)}. Tu laboratorio está listo.
          </h2>

          <p>
            Continúa tu formación práctica en ciberseguridad. Completa teoría,
            ejecuta el laboratorio, registra evidencias y recibe retroalimentación
            según tus checkpoints.
          </p>

          <div className="welcome-actions">
            <button className="btn hero-btn" onClick={openRecommended}>
              <Target size={17} />
              Continuar módulo recomendado
            </button>

            <button className="btn hero-btn secondary" onClick={() => setView('practice')}>
              <TerminalSquare size={17} />
              Abrir práctica local
            </button>

            <button className="btn hero-btn ghost-light" onClick={refreshDashboard}>
              <RefreshCw size={17} />
              Actualizar progreso
            </button>
          </div>
        </div>

        <ProgressRing value={generalPercent} />
      </section>

      <section className="student-kpi-grid">
        <Kpi
          icon={BookOpen}
          label="Módulos completados"
          value={`${completedModules}/${totalModules}`}
        />

        <Kpi
          icon={CheckCircle2}
          label="Checkpoints logrados"
          value={`${completedCheckpoints}/${totalCheckpoints}`}
        />

        <Kpi
          icon={Flame}
          label="Puntos acumulados"
          value={data.points || 0}
        />

        <Kpi
          icon={Award}
          label="Insignias obtenidas"
          value={data.badges || 0}
        />
      </section>

      <section className="student-dashboard-grid">
        <article className="card focus-module-card">
          <div className="dashboard-card-title">
            <div>
              <span className="badge">Siguiente paso</span>
              <h2>{recommended?.titulo || 'Módulo recomendado'}</h2>
              <p className="muted">
                Seleccionado automáticamente a partir de tu avance actual.
              </p>
            </div>

            <StatusPill percent={recommended?.progress?.percent || 0} />
          </div>

          <div className="focus-progress-row">
            <div className="focus-percent">
              <strong>{recommended?.progress?.percent || 0}%</strong>
              <span>avance del módulo</span>
            </div>

            <ProgressBar value={recommended?.progress?.percent || 0} />
          </div>

          <div className="focus-feedback-box">
            <Lightbulb size={22} />

            <div>
              <strong>
                {recommended?.feedback?.level || 'Recomendación inicial'}
              </strong>

              <p>
                {recommended?.feedback?.message ||
                  'Inicia el módulo para recibir retroalimentación personalizada.'}
              </p>
            </div>
          </div>

          <div className="recommended-actions-list">
            {(recommended?.feedback?.next_actions || [
              'Revisar la introducción del módulo.',
              'Ejecutar la práctica local controlada.',
              'Registrar evidencia del resultado obtenido.',
            ]).slice(0, 3).map((action) => (
              <div key={action}>
                <CheckCircle2 size={16} />
                <span>{action}</span>
              </div>
            ))}
          </div>

          <button className="btn full" onClick={openRecommended}>
            Continuar ahora
            <ChevronRight size={16} />
          </button>
        </article>

        <article className="card student-lab-card">
          <div className="dashboard-card-title">
            <div>
              <span className="badge">Laboratorio</span>
              <h2>Estado de práctica</h2>
            </div>

            <Activity size={26} />
          </div>

          <div className="lab-health-list">
            <div>
              <span>
                <TerminalSquare size={18} />
                Terminal guiada
              </span>
              <strong>Activa</strong>
            </div>

            <div>
              <span>
                <ShieldCheck size={18} />
                Entorno controlado
              </span>
              <strong>Seguro</strong>
            </div>

            <div>
              <span>
                <Clock3 size={18} />
                Última sincronización
              </span>
              <strong>Hace instantes</strong>
            </div>
          </div>

          <div className="terminal-preview-card">
            <div className="terminal-top">
              <span />
              <span />
              <span />
              <strong>cyberlab@practice</strong>
            </div>

            <pre>{`$ status --lab
✓ API conectada
✓ Ruta activa
✓ Evidencias disponibles
$ next --module ${recommended?.id || 'S02'}`}</pre>
          </div>

          <button className="btn secondary full" onClick={() => setView('practice')}>
            Iniciar práctica local
          </button>
        </article>
      </section>

      <section className="interactive-zone">
        <div className="interactive-tabs">
          <button
            className={selectedTab === 'ruta' ? 'active' : ''}
            onClick={() => setSelectedTab('ruta')}
          >
            Ruta interactiva
          </button>

          <button
            className={selectedTab === 'logros' ? 'active' : ''}
            onClick={() => setSelectedTab('logros')}
          >
            Logros
          </button>

          <button
            className={selectedTab === 'guia' ? 'active' : ''}
            onClick={() => setSelectedTab('guia')}
          >
            Guía rápida
          </button>
        </div>

        {selectedTab === 'ruta' && (
          <section className="card">
            <div className="dashboard-card-title">
              <div>
                <span className="badge">Ruta completa</span>
                <h2>Módulos de aprendizaje</h2>
                <p className="muted">
                  Explora tu avance y continúa desde el punto donde quedaste.
                </p>
              </div>

              <div className="mini-summary">
                <div>
                  <strong>{pendingModules}</strong>
                  <span>Pendientes</span>
                </div>

                <div>
                  <strong>{completedModules}</strong>
                  <span>Completados</span>
                </div>
              </div>
            </div>

            <div className="student-module-grid">
              {modules.map((module, index) => (
                <ModuleCard
                  key={module.id}
                  module={module}
                  index={index}
                  onOpen={openModule}
                />
              ))}
            </div>
          </section>
        )}

        {selectedTab === 'logros' && (
          <section className="card">
            <div className="dashboard-card-title">
              <div>
                <span className="badge">Gamificación</span>
                <h2>Logros y motivadores</h2>
                <p className="muted">
                  Estos indicadores ayudan a visualizar tu progreso durante la práctica.
                </p>
              </div>
            </div>

            <div className="achievement-grid">
              <Achievement
                icon={Sparkles}
                title="Primer acceso"
                description="Ingresaste con cuenta institucional."
                active
              />

              <Achievement
                icon={CheckCircle2}
                title="Checkpoints"
                description={`${completedCheckpoints} checkpoints completados.`}
                active={completedCheckpoints > 0}
              />

              <Achievement
                icon={Trophy}
                title="Ruta avanzada"
                description="Completa al menos 70% de la ruta."
                active={generalPercent >= 70}
              />

              <Achievement
                icon={Star}
                title="Explorador"
                description="Abre y revisa todos los módulos."
                active={completedModules === totalModules && totalModules > 0}
              />
            </div>
          </section>
        )}

        {selectedTab === 'guia' && (
          <section className="card">
            <div className="dashboard-card-title">
              <div>
                <span className="badge">Aprendizaje guiado</span>
                <h2>Cómo avanzar en CyberLab</h2>
                <p className="muted">
                  Sigue este flujo para completar cada experiencia práctica.
                </p>
              </div>
            </div>

            <div className="learning-flow">
              <TimelineStep
                number="1"
                title="Revisar teoría"
                description="Comprende el objetivo, conceptos y alcance del escenario."
                done={generalPercent > 0}
              />

              <TimelineStep
                number="2"
                title="Ejecutar laboratorio"
                description="Abre el entorno local y realiza la práctica controlada."
                active
              />

              <TimelineStep
                number="3"
                title="Completar checkpoints"
                description="Registra evidencias y valida los resultados esperados."
              />

              <TimelineStep
                number="4"
                title="Recibir retroalimentación"
                description="Analiza fortalezas, aspectos por reforzar y próximos pasos."
              />
            </div>
          </section>
        )}
      </section>

      <section className="student-bottom-grid">
        <article className="card insight-tile">
          <span>
            <Zap size={20} />
          </span>

          <div>
            <strong>Recomendación automática</strong>
            <p>
              Prioriza el módulo recomendado y completa los checkpoints pendientes
              antes de pasar al siguiente escenario.
            </p>
          </div>
        </article>

        <article className="card insight-tile">
          <span>
            <GraduationCap size={20} />
          </span>

          <div>
            <strong>Evidencia pedagógica</strong>
            <p>
              Tus avances, tiempos y respuestas alimentan el análisis formativo del
              simulador.
            </p>
          </div>
        </article>

        <article className="card insight-tile">
          <span>
            <ShieldCheck size={20} />
          </span>

          <div>
            <strong>Ambiente controlado</strong>
            <p>
              Las prácticas están pensadas para ejecutarse de forma segura y
              reproducible.
            </p>
          </div>
        </article>
      </section>
    </div>
  );
}