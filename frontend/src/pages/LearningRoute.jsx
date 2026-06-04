import { useEffect, useMemo, useState } from 'react';
import {
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  FileText,
  GraduationCap,
  Lightbulb,
  Loader2,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  TerminalSquare,
} from 'lucide-react';
import { ProgressBar } from '../components/Cards.jsx';
import { api } from '../lib/api.js';

function clamp(value = 0) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function cleanText(text = '') {
  return String(text)
    .replaceAll('Induccion', 'Inducción')
    .replaceAll('Autenticacion', 'Autenticación')
    .replaceAll('debil', 'débil')
    .replaceAll('Aplicacion', 'Aplicación')
    .replaceAll('practicas', 'prácticas')
    .replaceAll('Modulo', 'Módulo')
    .replaceAll('modulo', 'módulo')
    .replaceAll('etica', 'ética')
    .replaceAll('teoria', 'teoría')
    .replaceAll('practica', 'práctica')
    .replaceAll('evaluacion', 'evaluación')
    .replaceAll('ValleSec Lab', 'CyberLab');
}

function normalizeModules(payload) {
  if (Array.isArray(payload)) return payload;
  return payload?.modules || [];
}

function normalizeModule(payload) {
  const base = payload?.module || payload || {};
  return {
    ...base,
    progress: base.progress || payload?.progress || {},
    feedback: base.feedback || payload?.feedback || {},
    checkpoints: base.checkpoints || payload?.checkpoints || [],
    objetivos: base.objetivos || base.objectives || payload?.objetivos || [],
  };
}

function statusFromPercent(percent = 0) {
  if (percent >= 100) return { label: 'Completado', className: 'done' };
  if (percent > 0) return { label: 'En curso', className: 'progress' };
  return { label: 'Pendiente', className: 'pending' };
}

function ModuleCard({ module, active, onClick }) {
  const percent = clamp(module.progress?.percent);
  const status = statusFromPercent(percent);

  return (
    <button
      className={`route-pro-module-card ${active ? 'active' : ''}`}
      onClick={onClick}
    >
      <div>
        <strong>{cleanText(module.titulo || module.title)}</strong>
        <span className={`route-pro-status ${status.className}`}>
          {status.label}
        </span>
      </div>

      <ProgressBar value={percent} />

      <small>{percent}% de avance</small>
    </button>
  );
}

function PhaseButton({ icon: Icon, label, active, done, onClick }) {
  return (
    <button
      className={`route-pro-phase ${active ? 'active' : ''} ${done ? 'done' : ''}`}
      onClick={onClick}
    >
      <span>
        {done ? <CheckCircle2 size={18} /> : <Icon size={18} />}
      </span>
      <strong>{label}</strong>
    </button>
  );
}

function InfoBlock({ icon: Icon, title, children }) {
  return (
    <article className="route-pro-info-block">
      <span>
        <Icon size={20} />
      </span>

      <div>
        <strong>{title}</strong>
        <div>{children}</div>
      </div>
    </article>
  );
}

function CheckpointItem({ checkpoint, index, completed }) {
  const title = cleanText(
    checkpoint.titulo ||
      checkpoint.title ||
      checkpoint.nombre ||
      checkpoint.id ||
      `Checkpoint ${index + 1}`,
  );

  return (
    <div className={`route-pro-checkpoint ${completed ? 'done' : ''}`}>
      <span>
        {completed ? <CheckCircle2 size={18} /> : index + 1}
      </span>

      <div>
        <strong>{title}</strong>
        <small>
          {completed ? 'Evidencia registrada' : 'Pendiente por completar'}
        </small>
      </div>
    </div>
  );
}

function TheoryContent({ module }) {
  const description = cleanText(module.descripcion || module.description || '');
  const objetivos = module.objetivos || [];

  return (
    <div className="route-pro-content">
      <InfoBlock icon={GraduationCap} title="Propósito">
        <p>
          {description ||
            'Comprender el objetivo del módulo antes de ejecutar la práctica.'}
        </p>
      </InfoBlock>

      <InfoBlock icon={BookOpen} title="Contenido clave">
        <ul>
          {objetivos.length > 0 ? (
            objetivos.map((item) => (
              <li key={item}>{cleanText(item)}</li>
            ))
          ) : (
            <>
              <li>Reconocer el objetivo del escenario.</li>
              <li>Identificar reglas de uso del entorno controlado.</li>
              <li>Preparar la práctica antes de ejecutar comandos.</li>
            </>
          )}
        </ul>
      </InfoBlock>

      <InfoBlock icon={Lightbulb} title="Antes de continuar">
        <p>
          Revisa la teoría, identifica qué evidencia debes obtener y luego pasa al
          laboratorio local.
        </p>
      </InfoBlock>
    </div>
  );
}

function PracticeContent({ module, onPractice }) {
  return (
    <div className="route-pro-content">
      <div className="route-pro-lab-banner">
        <div>
          <span>Laboratorio local</span>
          <h3>{cleanText(module.titulo || 'Práctica guiada')}</h3>
          <p>
            Ejecuta el escenario asociado al módulo y registra evidencia desde la
            terminal guiada.
          </p>
        </div>

        <button className="route-pro-primary" onClick={onPractice}>
          <TerminalSquare size={17} />
          Abrir práctica
        </button>
      </div>

      <div className="route-pro-terminal-mini">
        <div className="route-pro-terminal-top">
          <span />
          <span />
          <span />
          <strong>cyberlab@lab</strong>
        </div>

        <pre>{`$ status --module ${module.id || 'M00'}
✓ Entorno controlado
✓ Terminal guiada
✓ Evidencia disponible`}</pre>
      </div>
    </div>
  );
}

function CheckpointsContent({ module }) {
  const checkpoints = module.checkpoints || [];
  const completed = module.progress?.completed_checkpoints || 0;

  return (
    <div className="route-pro-content">
      <div className="route-pro-checkpoint-grid">
        {checkpoints.length > 0 ? (
          checkpoints.map((checkpoint, index) => (
            <CheckpointItem
              key={checkpoint.id || index}
              checkpoint={checkpoint}
              index={index}
              completed={index < completed}
            />
          ))
        ) : (
          <>
            <CheckpointItem index={0} checkpoint={{ titulo: 'Revisar objetivos del módulo' }} />
            <CheckpointItem index={1} checkpoint={{ titulo: 'Ejecutar práctica guiada' }} />
            <CheckpointItem index={2} checkpoint={{ titulo: 'Registrar evidencia mínima' }} />
          </>
        )}
      </div>
    </div>
  );
}

function EvaluationContent({ module }) {
  const feedback = module.feedback || {};

  return (
    <div className="route-pro-content">
      <div className="route-pro-feedback-card">
        <Lightbulb size={24} />

        <div>
          <strong>{feedback.level || 'Retroalimentación pendiente'}</strong>
          <p>
            {feedback.message ||
              'Completa los checkpoints del módulo para recibir una retroalimentación más precisa.'}
          </p>
        </div>
      </div>

      <InfoBlock icon={ClipboardCheck} title="Cierre del módulo">
        <p>
          Al finalizar, revisa tus resultados, completa la encuesta post-sesión y
          valida qué conceptos debes reforzar.
        </p>
      </InfoBlock>
    </div>
  );
}

export default function LearningRoute({
  selectedModule,
  setSelectedModule,
  refreshDashboard,
  userId,
  setView,
}) {
  const [modules, setModules] = useState([]);
  const [moduleData, setModuleData] = useState(null);
  const [activePhase, setActivePhase] = useState('theory');
  const [loading, setLoading] = useState(true);

  const moduleId = selectedModule || modules[0]?.id || 'M00';

  useEffect(() => {
    async function loadModules() {
      try {
        const payload = await api.modules();
        const items = normalizeModules(payload);
        setModules(items);

        if (!selectedModule && items[0]?.id) {
          setSelectedModule(items[0].id);
        }
      } catch (error) {
        console.error(error);
      }
    }

    loadModules();
  }, []);

  useEffect(() => {
    async function loadModule() {
      if (!moduleId) return;

      try {
        setLoading(true);
        const payload = await api.module(moduleId, userId);
        setModuleData(normalizeModule(payload));
      } catch (error) {
        console.error(error);
      } finally {
        setLoading(false);
      }
    }

    loadModule();
  }, [moduleId, userId]);

  const activeModule = moduleData || modules.find((item) => item.id === moduleId) || {};
  const progress = activeModule.progress || {};
  const percent = clamp(progress.percent);
  const completed = progress.completed_checkpoints || 0;
  const total = progress.total_checkpoints || activeModule.checkpoints?.length || 0;

  const phaseState = useMemo(() => ({
    theory: percent > 0,
    practice: completed > 0,
    checkpoints: total > 0 && completed >= total,
    evaluation: percent >= 100,
  }), [percent, completed, total]);

  function changeModule(id) {
    setSelectedModule(id);
    setActivePhase('theory');
  }

  function goPractice() {
    setView?.('practice');
  }

  function goResults() {
    refreshDashboard?.();
    setView?.('results');
  }

  return (
    <div className="route-pro-page">
      <section className="route-pro-hero">
        <div>
          <span className="route-pro-chip">
            <ShieldCheck size={15} />
            Ruta del estudiante
          </span>

          <h2>Aprende, practica y valida tu avance</h2>

          <p>
            Cada módulo combina teoría breve, laboratorio guiado, checkpoints y
            retroalimentación formativa.
          </p>
        </div>

        <div className="route-pro-summary">
          <strong>{percent}%</strong>
          <span>avance del módulo</span>
          <ProgressBar value={percent} />
          <small>{completed}/{total} checkpoints</small>
        </div>
      </section>

      <section className="route-pro-layout">
        <aside className="route-pro-sidebar">
          <div className="route-pro-sidebar-title">
            <span>Módulos</span>
            <button onClick={refreshDashboard} title="Actualizar">
              <RefreshCw size={16} />
            </button>
          </div>

          <div className="route-pro-modules">
            {modules.map((module) => (
              <ModuleCard
                key={module.id}
                module={module}
                active={module.id === moduleId}
                onClick={() => changeModule(module.id)}
              />
            ))}
          </div>
        </aside>

        <main className="route-pro-main">
          {loading ? (
            <div className="route-pro-loading">
              <Loader2 size={24} className="spin" />
              Cargando módulo...
            </div>
          ) : (
            <>
              <div className="route-pro-module-head">
                <div>
                  <span className="route-pro-chip">Módulo actual</span>
                  <h2>{cleanText(activeModule.titulo || activeModule.title)}</h2>
                  <p>{cleanText(activeModule.descripcion || activeModule.description)}</p>
                </div>

                <button className="route-pro-outline" onClick={goResults}>
                  Ver resultados
                  <ChevronRight size={16} />
                </button>
              </div>

              <div className="route-pro-phases">
                <PhaseButton
                  icon={BookOpen}
                  label="Teoría"
                  active={activePhase === 'theory'}
                  done={phaseState.theory}
                  onClick={() => setActivePhase('theory')}
                />

                <PhaseButton
                  icon={TerminalSquare}
                  label="Práctica"
                  active={activePhase === 'practice'}
                  done={phaseState.practice}
                  onClick={() => setActivePhase('practice')}
                />

                <PhaseButton
                  icon={ClipboardCheck}
                  label="Checkpoints"
                  active={activePhase === 'checkpoints'}
                  done={phaseState.checkpoints}
                  onClick={() => setActivePhase('checkpoints')}
                />

                <PhaseButton
                  icon={Lightbulb}
                  label="Evaluación"
                  active={activePhase === 'evaluation'}
                  done={phaseState.evaluation}
                  onClick={() => setActivePhase('evaluation')}
                />
              </div>

              {activePhase === 'theory' && <TheoryContent module={activeModule} />}
              {activePhase === 'practice' && (
                <PracticeContent module={activeModule} onPractice={goPractice} />
              )}
              {activePhase === 'checkpoints' && (
                <CheckpointsContent module={activeModule} />
              )}
              {activePhase === 'evaluation' && (
                <EvaluationContent module={activeModule} />
              )}
            </>
          )}
        </main>
      </section>
    </div>
  );
}