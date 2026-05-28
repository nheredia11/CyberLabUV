import { useMemo } from 'react';
import {
  Activity,
  AlertCircle,
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  FileText,
  Flame,
  GraduationCap,
  Lightbulb,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Target,
  TerminalSquare,
  Trophy,
  Zap,
} from 'lucide-react';
import { Kpi, ProgressBar } from '../components/Cards.jsx';

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

function moduleStatus(percent = 0) {
  if (percent >= 100) return { label: 'Completado', className: 'done' };
  if (percent >= 60) return { label: 'Avanzado', className: 'progress' };
  if (percent > 0) return { label: 'En progreso', className: 'started' };
  return { label: 'Pendiente', className: 'pending' };
}

function StatusPill({ percent }) {
  const status = moduleStatus(percent);

  return (
    <span className={`status-pill ${status.className}`}>
      {status.label}
    </span>
  );
}

function ProgressCircle({ value = 0 }) {
  const percent = clamp(value);
  const degrees = percent * 3.6;

  return (
    <div className="student-circle-wrap">
      <div
        className="student-circle"
        style={{
          background: `conic-gradient(var(--accent) ${degrees}deg, rgba(255,255,255,.18) 0deg)`,
        }}
      >
        <div>
          <strong>{percent}%</strong>
          <span>ruta</span>
        </div>
      </div>
    </div>
  );
}

function MissionStep({ icon: Icon, title, done, active }) {
  return (
    <div className={`mission-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
      <span>
        {done ? <CheckCircle2 size={16} /> : <Icon size={16} />}
      </span>
      <strong>{title}</strong>
    </div>
  );
}

function RouteStep({ icon: Icon, title, description, done, active }) {
  return (
    <div className={`route-step ${done ? 'done' : ''} ${active ? 'active' : ''}`}>
      <span>
        {done ? <CheckCircle2 size={18} /> : <Icon size={18} />}
      </span>

      <div>
        <strong>{title}</strong>
        <small>{description}</small>
      </div>
    </div>
  );
}

function ModuleMiniCard({ module, index, onOpen }) {
  const percent = clamp(module.progress?.percent);
  const completed = module.progress?.completed_checkpoints || 0;
  const total = module.progress?.total_checkpoints || 0;

  return (
    <button className="module-mini-card" onClick={() => onOpen(module.id)}>
      <div className="module-mini-top">
        <span className="module-mini-index">{String(index + 1).padStart(2, '0')}</span>
        <StatusPill percent={percent} />
      </div>

      <strong>{module.titulo}</strong>

      <ProgressBar value={percent} />

      <div className="module-mini-bottom">
        <span>{percent}% avance</span>
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

  const currentModulePercent = clamp(recommended?.progress?.percent);
  const currentCompleted = recommended?.progress?.completed_checkpoints || 0;
  const currentTotal = recommended?.progress?.total_checkpoints || 0;
  const hasStarted = currentModulePercent > 0;
  const isModuleDone = currentModulePercent >= 100;

  function openModule(moduleId) {
    setSelectedModule(moduleId);
    setView('route');
  }

  function openRecommended() {
    openModule(recommended?.id || 'S02');
  }

  if (!data) {
    return (
      <div className="student-dashboard-v2">
        <section className="student-loading-card">
          <div className="student-loading-icon" />
          <div>
            <h3>Cargando tu ruta de aprendizaje...</h3>
            <p>Estamos consultando módulos, progreso y recomendaciones.</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="student-dashboard-v2">
      <section className="student-overview-hero">
        <div className="overview-copy">
          <span className="overview-badge">
            <ShieldCheck size={15} />
            Sesión institucional activa
          </span>

          <h2>
            Hola, {firstName(user?.name)}. Continúa tu práctica en CyberLab.
          </h2>

          <p>
            Tu siguiente paso está organizado para que avances por teoría, práctica,
            checkpoints y retroalimentación sin perder el hilo del laboratorio.
          </p>

          <div className="overview-actions">
            <button className="btn hero-btn" onClick={openRecommended}>
              <Target size={17} />
              Continuar ahora
            </button>

            <button className="btn hero-btn secondary" onClick={() => setView('practice')}>
              <TerminalSquare size={17} />
              Abrir laboratorio
            </button>

            <button className="btn hero-btn ghost-light" onClick={refreshDashboard}>
              <RefreshCw size={17} />
              Actualizar
            </button>
          </div>
        </div>

        <div className="overview-progress-panel">
          <ProgressCircle value={generalPercent} />
          <strong>Progreso general</strong>
          <span>{completedModules}/{totalModules} módulos completados</span>
        </div>
      </section>

      <section className="student-kpi-grid compact">
        <Kpi
          icon={BookOpen}
          label="Módulos"
          value={`${completedModules}/${totalModules}`}
        />

        <Kpi
          icon={ClipboardCheck}
          label="Checkpoints"
          value={`${completedCheckpoints}/${totalCheckpoints}`}
        />

        <Kpi
          icon={Flame}
          label="Puntos"
          value={data.points || 0}
        />

        <Kpi
          icon={Award}
          label="Insignias"
          value={data.badges || 0}
        />
      </section>

      <section className="student-main-grid-v2">
        <article className="card mission-card">
          <div className="mission-header">
            <div>
              <span className="badge">Tu misión actual</span>
              <h2>{recommended?.titulo || 'Módulo recomendado'}</h2>
              <p>
                Este es el módulo que deberías continuar según tu avance actual.
              </p>
            </div>

            <StatusPill percent={currentModulePercent} />
          </div>

          <div className="mission-progress">
            <div>
              <strong>{currentModulePercent}%</strong>
              <span>avance del módulo</span>
            </div>

            <ProgressBar value={currentModulePercent} />
          </div>

          <div className="mission-steps">
            <MissionStep
              icon={BookOpen}
              title="Teoría"
              done={hasStarted || isModuleDone}
              active={!hasStarted}
            />

            <MissionStep
              icon={TerminalSquare}
              title="Práctica"
              done={currentCompleted > 0}
              active={hasStarted && currentCompleted === 0}
            />

            <MissionStep
              icon={ClipboardCheck}
              title="Checkpoints"
              done={currentCompleted >= currentTotal && currentTotal > 0}
              active={currentCompleted > 0 && currentCompleted < currentTotal}
            />

            <MissionStep
              icon={Lightbulb}
              title="Retroalimentación"
              done={isModuleDone}
              active={currentCompleted >= currentTotal && currentTotal > 0}
            />
          </div>

          <div className="mission-feedback">
            <Lightbulb size={22} />

            <div>
              <strong>{recommended?.feedback?.level || 'Recomendación inicial'}</strong>
              <p>
                {recommended?.feedback?.message ||
                  'Comienza revisando la teoría del módulo y luego ejecuta la práctica guiada.'}
              </p>
            </div>
          </div>

          <div className="mission-actions">
            <button className="btn full" onClick={openRecommended}>
              Ir al módulo
              <ChevronRight size={16} />
            </button>

            <button className="btn secondary full" onClick={() => setView('results')}>
              Ver retroalimentación
            </button>
          </div>
        </article>

        <aside className="student-side-stack">
          <article className="card lab-ready-card">
            <div className="side-title">
              <span className="badge">Laboratorio</span>
              <Activity size={24} />
            </div>

            <h2>Estado del entorno</h2>

            <div className="lab-readiness">
              <div>
                <TerminalSquare size={18} />
                <span>Terminal guiada</span>
                <strong>Lista</strong>
              </div>

              <div>
                <ShieldCheck size={18} />
                <span>Entorno controlado</span>
                <strong>Seguro</strong>
              </div>

              <div>
                <FileText size={18} />
                <span>Evidencias</span>
                <strong>Disponibles</strong>
              </div>
            </div>

            <button className="btn secondary full" onClick={() => setView('practice')}>
              Abrir práctica local
            </button>
          </article>

          <article className="card student-tip-card">
            <span>
              <Zap size={20} />
            </span>

            <div>
              <strong>Consejo para avanzar</strong>
              <p>
                Completa primero los objetivos del módulo antes de ejecutar varios
                comandos. Así la evidencia queda más clara.
              </p>
            </div>
          </article>
        </aside>
      </section>

      <section className="card route-map-card">
        <div className="route-map-header">
          <div>
            <span className="badge">Ruta de aprendizaje</span>
            <h2>Flujo recomendado</h2>
            <p>
              Cada módulo sigue una secuencia corta para conectar teoría, laboratorio
              y evidencia.
            </p>
          </div>

          <button className="btn ghost" onClick={() => setView('route')}>
            Ver ruta completa
          </button>
        </div>

        <div className="route-flow">
          <RouteStep
            icon={GraduationCap}
            title="1. Comprender"
            description="Lee la teoría y el objetivo del escenario."
            done={generalPercent > 0}
            active={generalPercent === 0}
          />

          <RouteStep
            icon={TerminalSquare}
            title="2. Practicar"
            description="Ejecuta el laboratorio local controlado."
            active={generalPercent > 0 && generalPercent < 50}
          />

          <RouteStep
            icon={ClipboardCheck}
            title="3. Evidenciar"
            description="Completa checkpoints y registra resultados."
            active={generalPercent >= 50 && generalPercent < 100}
          />

          <RouteStep
            icon={Trophy}
            title="4. Mejorar"
            description="Revisa retroalimentación y refuerza conceptos."
            done={generalPercent >= 100}
          />
        </div>
      </section>

      <section className="card modules-overview-card">
        <div className="route-map-header">
          <div>
            <span className="badge">Módulos disponibles</span>
            <h2>Tu avance por escenario</h2>
          </div>
        </div>

        <div className="modules-mini-grid">
          {modules.map((module, index) => (
            <ModuleMiniCard
              key={module.id}
              module={module}
              index={index}
              onOpen={openModule}
            />
          ))}
        </div>
      </section>
    </div>
  );
}