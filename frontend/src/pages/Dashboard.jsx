import { useMemo } from 'react';
import {
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Flame,
  GraduationCap,
  Lightbulb,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Target,
  TerminalSquare,
  Trophy,
  UserRound,
} from 'lucide-react';
import { ProgressBar } from '../components/Cards.jsx';

function clamp(value = 0) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function firstName(name = '') {
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
  if (percent >= 100) return { label: 'Completado', className: 'done' };
  if (percent >= 60) return { label: 'Avanzado', className: 'progress' };
  if (percent > 0) return { label: 'En curso', className: 'started' };
  return { label: 'Pendiente', className: 'pending' };
}

function StatusPill({ percent }) {
  const status = getStatus(percent);

  return (
    <span className={`dash-status ${status.className}`}>
      {status.label}
    </span>
  );
}

function MetricCard({ icon: Icon, value, label }) {
  return (
    <article className="dash-metric-card">
      <span>
        <Icon size={22} />
      </span>

      <div>
        <strong>{value}</strong>
        <small>{label}</small>
      </div>
    </article>
  );
}

function ProgressCircle({ value = 0 }) {
  const percent = clamp(value);
  const deg = percent * 3.6;

  return (
    <div className="dash-progress-circle">
      <div
        className="dash-progress-ring"
        style={{
          background: `conic-gradient(var(--accent) ${deg}deg, rgba(255,255,255,.22) 0deg)`,
        }}
      >
        <div>
          <strong>{percent}%</strong>
          <span>avance</span>
        </div>
      </div>
    </div>
  );
}

function StepItem({ icon: Icon, label, active, done }) {
  return (
    <div className={`dash-step ${active ? 'active' : ''} ${done ? 'done' : ''}`}>
      <span>
        {done ? <CheckCircle2 size={16} /> : <Icon size={16} />}
      </span>
      <strong>{label}</strong>
    </div>
  );
}

function ModuleCard({ module, index, onOpen, selected }) {
  const percent = clamp(module.progress?.percent);
  const completed = module.progress?.completed_checkpoints || 0;
  const total = module.progress?.total_checkpoints || 0;

  return (
    <button
      className={`dash-module-card ${selected ? 'selected' : ''}`}
      onClick={() => onOpen(module.id)}
    >
      <div className="dash-module-head">
        <span className="dash-module-index">{String(index + 1).padStart(2, '0')}</span>
        <StatusPill percent={percent} />
      </div>

      <h3>{module.titulo}</h3>

      <ProgressBar value={percent} />

      <div className="dash-module-foot">
        <span>{percent}%</span>
        <span>{completed}/{total} checkpoints</span>
      </div>
    </button>
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
  const modules = data?.modules || [];

  const recommended = useMemo(() => getRecommendedModule(modules), [modules]);

  const generalPercent = clamp(data?.general_percent);
  const completedModules = data?.completed_modules || 0;
  const totalModules = data?.total_modules || modules.length || 0;

  const completedCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.completed_checkpoints || 0),
    0,
  );

  const totalCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.total_checkpoints || 0),
    0,
  );

  const currentPercent = clamp(recommended?.progress?.percent);
  const currentCompleted = recommended?.progress?.completed_checkpoints || 0;
  const currentTotal = recommended?.progress?.total_checkpoints || 0;

  const theoryDone = currentPercent > 0;
  const practiceDone = currentCompleted > 0;
  const checkpointsDone = currentTotal > 0 && currentCompleted >= currentTotal;
  const feedbackReady = checkpointsDone || currentPercent >= 100;

  function openModule(moduleId) {
    setSelectedModule(moduleId);
    setView('route');
  }

  function openRecommended() {
    openModule(recommended?.id || 'S02');
  }

  if (!data) {
    return (
      <div className="dash-student">
        <section className="dash-loading">
          <div className="dash-loading-icon" />
          <div>
            <h3>Cargando tu espacio de aprendizaje...</h3>
            <p>Estamos preparando tus módulos y avances.</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="dash-student">
      <section className="dash-hero">
        <div className="dash-hero-copy">
          <span className="dash-badge">
            <ShieldCheck size={15} />
            Sesión institucional activa
          </span>

          <h1>
            Hola, {firstName(user?.name)}. Sigue tu práctica en CyberLab.
          </h1>

          <p>
            Tu ruta está organizada por módulos, práctica local, checkpoints y retroalimentación.
          </p>

          <div className="dash-hero-actions">
            <button className="dash-primary-btn" onClick={openRecommended}>
              <Target size={17} />
              Continuar
            </button>

            <button className="dash-secondary-btn" onClick={() => setView('practice')}>
              <TerminalSquare size={17} />
              Laboratorio
            </button>

            <button className="dash-ghost-btn" onClick={refreshDashboard}>
              <RefreshCw size={17} />
              Actualizar
            </button>
          </div>
        </div>

        <div className="dash-hero-progress">
          <ProgressCircle value={generalPercent} />
          <strong>Progreso general</strong>
          <span>{completedModules}/{totalModules} módulos</span>
        </div>
      </section>

      <section className="dash-metrics">
        <MetricCard
          icon={BookOpen}
          value={`${completedModules}/${totalModules}`}
          label="Módulos"
        />

        <MetricCard
          icon={ClipboardCheck}
          value={`${completedCheckpoints}/${totalCheckpoints}`}
          label="Checkpoints"
        />

        <MetricCard
          icon={Flame}
          value={data.points || 0}
          label="Puntos"
        />

        <MetricCard
          icon={Award}
          value={data.badges || 0}
          label="Insignias"
        />
      </section>

      <section className="dash-layout">
        <article className="dash-card dash-current-module">
          <div className="dash-card-head">
            <div>
              <span className="dash-mini-label">Misión actual</span>
              <h2>{recommended?.titulo || 'Módulo recomendado'}</h2>
            </div>

            <StatusPill percent={currentPercent} />
          </div>

          <div className="dash-module-progress-row">
            <strong>{currentPercent}%</strong>
            <ProgressBar value={currentPercent} />
          </div>

          <div className="dash-steps">
            <StepItem icon={GraduationCap} label="Teoría" done={theoryDone} active={!theoryDone} />
            <StepItem icon={TerminalSquare} label="Práctica" done={practiceDone} active={theoryDone && !practiceDone} />
            <StepItem icon={ClipboardCheck} label="Evidencia" done={checkpointsDone} active={practiceDone && !checkpointsDone} />
            <StepItem icon={Lightbulb} label="Feedback" done={feedbackReady} active={checkpointsDone && !feedbackReady} />
          </div>

          <div className="dash-feedback-box">
            <Lightbulb size={21} />

            <div>
              <strong>{recommended?.feedback?.level || 'Pendiente'}</strong>
              <p>
                {recommended?.feedback?.message ||
                  'Empieza por revisar la teoría y luego ejecuta el laboratorio guiado.'}
              </p>
            </div>
          </div>

          <div className="dash-card-actions">
            <button className="dash-primary-btn full" onClick={openRecommended}>
              Ir al módulo
              <ChevronRight size={16} />
            </button>

            <button className="dash-secondary-btn full" onClick={() => setView('results')}>
              Ver resultados
            </button>
          </div>
        </article>

        <aside className="dash-side">
          <article className="dash-card dash-account">
            <div className="dash-account-top">
              {user?.picture ? (
                <img src={user.picture} alt={user.name} />
              ) : (
                <span>
                  <UserRound size={22} />
                </span>
              )}

              <div>
                <strong>{user?.name}</strong>
                <small>{user?.email}</small>
              </div>
            </div>

            <div className="dash-account-meta">
              <span>Rol</span>
              <strong>{user?.role === 'teacher' ? 'Docente' : 'Estudiante'}</strong>
            </div>

            <div className="dash-account-meta">
              <span>ID de sesión</span>
              <strong>{userId}</strong>
            </div>
          </article>

          <article className="dash-card dash-lab">
            <div className="dash-card-head compact">
              <div>
                <span className="dash-mini-label">Laboratorio</span>
                <h2>Listo para practicar</h2>
              </div>
            </div>

            <div className="dash-lab-items">
              <div>
                <TerminalSquare size={18} />
                <span>Terminal guiada</span>
                <strong>Lista</strong>
              </div>

              <div>
                <ShieldCheck size={18} />
                <span>Ambiente</span>
                <strong>Seguro</strong>
              </div>

              <div>
                <Clock3 size={18} />
                <span>Sincronización</span>
                <strong>Activa</strong>
              </div>
            </div>

            <button className="dash-secondary-btn full" onClick={() => setView('practice')}>
              Abrir práctica local
            </button>
          </article>
        </aside>
      </section>

      <section className="dash-card dash-route">
        <div className="dash-route-head">
          <div>
            <span className="dash-mini-label">Ruta de aprendizaje</span>
            <h2>Avance por escenario</h2>
          </div>

          <button className="dash-ghost-link" onClick={() => setView('route')}>
            Ver ruta completa
            <ChevronRight size={16} />
          </button>
        </div>

        <div className="dash-modules-grid">
          {modules.map((module, index) => (
            <ModuleCard
              key={module.id}
              module={module}
              index={index}
              selected={module.id === recommended?.id}
              onOpen={openModule}
            />
          ))}
        </div>
      </section>

      <section className="dash-bottom-grid">
        <article className="dash-note">
          <span>
            <PlayCircle size={20} />
          </span>

          <div>
            <strong>Practica con propósito</strong>
            <p>Lee el objetivo, ejecuta el laboratorio y registra evidencia clara.</p>
          </div>
        </article>

        <article className="dash-note">
          <span>
            <Trophy size={20} />
          </span>

          <div>
            <strong>Completa checkpoints</strong>
            <p>Los checkpoints muestran tu avance real en cada escenario.</p>
          </div>
        </article>

        <article className="dash-note">
          <span>
            <Lightbulb size={20} />
          </span>

          <div>
            <strong>Revisa el feedback</strong>
            <p>La retroalimentación te ayuda a reforzar conceptos antes de avanzar.</p>
          </div>
        </article>
      </section>
    </div>
  );
}