import {
  AlertCircle,
  Award,
  BookOpen,
  CheckCircle2,
  ClipboardCheck,
  Download,
  FileText,
  Lightbulb,
  ListChecks,
  RefreshCw,
  Target,
  TrendingUp,
} from 'lucide-react';

// NUEVO: Componente ProgressBar integrado para independizar este archivo
function ProgressBar({ value }) {
  const percent = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div style={{ width: '100%', backgroundColor: '#21262d', borderRadius: '4px', height: '8px', overflow: 'hidden', margin: '8px 0' }}>
      <div 
        style={{ 
          height: '100%', 
          backgroundColor: percent >= 85 ? '#3fb950' : percent >= 50 ? '#d2a8ff' : '#58a6ff', 
          width: `${percent}%`,
          transition: 'width 0.4s ease-in-out'
        }} 
      />
    </div>
  );
}

function clamp(value = 0) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function firstName(name = '') {
  return name?.split(' ')?.[0] || 'estudiante';
}

function cleanTitle(title = '') {
  return title
    .replaceAll('Induccion', 'Inducción')
    .replaceAll('Autenticacion', 'Autenticación')
    .replaceAll('debil', 'débil')
    .replaceAll('Aplicacion', 'Aplicación')
    .replaceAll('practicas', 'prácticas')
    .replaceAll('etica', 'ética')
    .replaceAll('teoria', 'teoría')
    .replaceAll('practica', 'práctica')
    .replaceAll('evaluacion', 'evaluación');
}

function getLevel(percent) {
  if (percent >= 85) return { label: 'Alto', className: 'high', color: '#3fb950' };
  if (percent >= 50) return { label: 'En progreso', className: 'mid', color: '#d2a8ff' };
  if (percent > 0) return { label: 'Inicial', className: 'low', color: '#58a6ff' };
  return { label: 'Sin iniciar', className: 'empty', color: '#8b949e' };
}

function ResultMetric({ icon: Icon, label, value, detail }) {
  return (
    <article className="report-metric" style={{ background: '#161b22', padding: '15px', borderRadius: '8px', border: '1px solid #30363d', display: 'flex', gap: '15px', alignItems: 'center' }}>
      <span style={{ background: '#21262d', padding: '10px', borderRadius: '8px', color: '#c9d1d9', display: 'flex' }}>
        <Icon size={20} />
      </span>
      <div style={{ display: 'flex', flexDirection: 'column' }}>
        <strong style={{ fontSize: '20px', color: '#c9d1d9' }}>{value}</strong>
        <small style={{ color: '#8b949e', fontSize: '12px' }}>{label}</small>
        {detail && <em style={{ fontSize: '11px', color: '#8b949e', fontStyle: 'normal' }}>{detail}</em>}
      </div>
    </article>
  );
}

function IndicatorRow({ title, value, description }) {
  const percent = clamp(value);
  const level = getLevel(percent);

  return (
    <div className="report-indicator-row" style={{ marginBottom: '15px' }}>
      <div className="report-indicator-head" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '5px' }}>
        <div>
          <strong style={{ color: '#c9d1d9', display: 'block' }}>{title}</strong>
          <small style={{ color: '#8b949e', fontSize: '12px' }}>{description}</small>
        </div>
        <span style={{ fontSize: '12px', fontWeight: 'bold', color: level.color }}>
          {level.label}
        </span>
      </div>
      <ProgressBar value={percent} />
      <div className="report-indicator-percent" style={{ textAlign: 'right', fontSize: '12px', color: '#8b949e' }}>
        <span>{percent}%</span>
      </div>
    </div>
  );
}

function ModuleResultItem({ module }) {
  const percent = clamp(module.progress?.percent);
  const completed = module.progress?.completed_checkpoints || 0;
  const total = module.progress?.total_checkpoints || 0;
  const level = getLevel(percent);

  return (
    <article className="report-module-item" style={{ background: '#161b22', padding: '15px', borderRadius: '8px', border: '1px solid #30363d', marginBottom: '15px' }}>
      <div className="report-module-main" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
        <div>
          <strong style={{ color: '#c9d1d9', display: 'block' }}>{cleanTitle(module.titulo)}</strong>
          <small style={{ color: '#8b949e' }}>{completed}/{total} checkpoints</small>
        </div>
        <span style={{ fontSize: '12px', fontWeight: 'bold', color: level.color }}>
          {level.label}
        </span>
      </div>

      <ProgressBar value={percent} />

      <div className="report-module-foot" style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: '#8b949e', marginTop: '10px' }}>
        <span>{percent}% completado</span>
        <span style={{ color: module.progress?.survey_completed ? '#3fb950' : '#8b949e' }}>
          {module.progress?.survey_completed ? 'Encuesta realizada' : 'Encuesta pendiente'}
        </span>
      </div>
    </article>
  );
}

function NextStep({ number, title, description }) {
  return (
    <article className="report-next-step" style={{ display: 'flex', gap: '15px', background: '#0d1117', padding: '15px', borderRadius: '8px', border: '1px solid #30363d' }}>
      <span style={{ background: '#1f6feb', color: '#fff', width: '30px', height: '30px', display: 'flex', alignItems: 'center', justifyContent: 'center', borderRadius: '50%', fontWeight: 'bold', flexShrink: 0 }}>
        {number}
      </span>
      <div>
        <strong style={{ color: '#c9d1d9', display: 'block', marginBottom: '5px' }}>{title}</strong>
        <p style={{ margin: 0, color: '#8b949e', fontSize: '13px' }}>{description}</p>
      </div>
    </article>
  );
}

export default function Results({ data, user, setView }) {
  const modules = data?.modules || [];
  const studentName = firstName(user?.name);

  const totalModules = data?.total_modules || modules.length || 0;
  const completedModules = data?.completed_modules || 0;
  const generalPercent = clamp(data?.general_percent);

  const completedCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.completed_checkpoints || 0),
    0,
  );

  const totalCheckpoints = modules.reduce(
    (acc, module) => acc + (module.progress?.total_checkpoints || 0),
    0,
  );

  const completedSurveys = modules.filter(
    (module) => module.progress?.survey_completed,
  ).length;

  const activeModules = modules.filter(
    (module) => clamp(module.progress?.percent) > 0,
  ).length;

  const checkpointPercent = totalCheckpoints
    ? Math.round((completedCheckpoints / totalCheckpoints) * 100)
    : 0;

  const surveyPercent = totalModules
    ? Math.round((completedSurveys / totalModules) * 100)
    : 0;

  const continuityPercent = totalModules
    ? Math.round((activeModules / totalModules) * 100)
    : 0;

  const pendingCheckpoints = Math.max(totalCheckpoints - completedCheckpoints, 0);

  const currentModule =
    modules.find((module) => module.progress?.percent > 0 && module.progress?.percent < 100) ||
    modules.find((module) => module.progress?.percent === 0) ||
    modules[0];

  const level = getLevel(generalPercent);

  const feedbackTitle =
    generalPercent >= 85
      ? 'Buen desempeño'
      : generalPercent >= 50
        ? 'Vas avanzando'
        : generalPercent > 0
          ? 'Primer avance registrado'
          : 'Ruta pendiente por iniciar';

  const feedbackText =
    generalPercent >= 85
      ? 'El avance es sólido. Prioriza cerrar evidencias pendientes y revisar la retroalimentación final.'
      : generalPercent >= 50
        ? 'El proceso va bien. Completa los checkpoints pendientes y registra evidencia clara de la práctica.'
        : generalPercent > 0
          ? 'Ya iniciaste la ruta. Continúa con el módulo actual y valida tus primeros checkpoints.'
          : 'Empieza por el módulo de inducción para comprender el entorno, las reglas de uso y la dinámica de práctica.';

  if (!data) {
    return (
      <div className="results-report-page" style={{ padding: '40px', textAlign: 'center', color: '#8b949e' }}>
        <h3>Cargando resultados...</h3>
        <p>Estamos preparando tu retroalimentación.</p>
      </div>
    );
  }

  return (
    <div className="results-report-page" style={{ maxWidth: '1000px', margin: '0 auto', padding: '20px' }}>
      
      {/* HEADER */}
      <section className="results-report-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '30px', paddingBottom: '20px', borderBottom: '1px solid #30363d' }}>
        <div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '12px', background: '#21262d', color: '#c9d1d9', padding: '4px 10px', borderRadius: '12px', marginBottom: '10px' }}>
            <FileText size={15} /> Informe formativo
          </span>
          <h2 style={{ margin: '0 0 10px 0', color: '#c9d1d9', fontSize: '24px' }}>Resultados de {studentName}</h2>
          <p style={{ margin: 0, color: '#8b949e' }}>Resumen de desempeño, evidencias y recomendaciones.</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button onClick={() => window.print()} style={{ padding: '8px 15px', background: 'transparent', color: '#58a6ff', border: '1px solid #30363d', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
            <Download size={16} /> Exportar
          </button>
        </div>
      </section>

      {/* SUMMARY CARD */}
      <section className="report-summary-card" style={{ background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d', display: 'flex', justifyContent: 'space-between', marginBottom: '30px' }}>
        <div style={{ flex: 1, paddingRight: '20px' }}>
          <span style={{ color: level.color, fontWeight: 'bold', fontSize: '12px', textTransform: 'uppercase' }}>{level.label}</span>
          <h3 style={{ color: '#c9d1d9', margin: '10px 0' }}>{feedbackTitle}</h3>
          <p style={{ color: '#8b949e', margin: 0, lineHeight: '1.5' }}>{feedbackText}</p>
        </div>
        <div style={{ width: '250px', background: '#0d1117', padding: '20px', borderRadius: '8px', border: '1px solid #30363d', textAlign: 'center' }}>
          <strong style={{ fontSize: '32px', color: '#c9d1d9', display: 'block' }}>{generalPercent}%</strong>
          <span style={{ color: '#8b949e', fontSize: '13px', display: 'block', marginBottom: '10px' }}>Avance general</span>
          <ProgressBar value={generalPercent} />
          <small style={{ color: '#8b949e', fontSize: '11px', display: 'block', marginTop: '10px' }}>{completedModules}/{totalModules} módulos completados</small>
        </div>
      </section>

      {/* METRICS GRID */}
      <section className="report-metrics-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '15px', marginBottom: '30px' }}>
        <ResultMetric icon={BookOpen} value={`${completedModules}/${totalModules}`} label="Módulos" detail="avance de la ruta" />
        <ResultMetric icon={ClipboardCheck} value={`${completedCheckpoints}/${totalCheckpoints}`} label="Checkpoints" detail="evidencias validadas" />
        <ResultMetric icon={Award} value={data?.badges || 0} label="Insignias" detail="logros obtenidos" />
        <ResultMetric icon={TrendingUp} value={data?.points || 0} label="Puntos" detail="acumulados" />
      </section>

      {/* DETAILED PANELS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', marginBottom: '30px' }}>
        
        {/* PANEL IZQUIERDO: Feedback */}
        <article className="report-panel" style={{ background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', margin: '0 0 20px 0', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>Retroalimentación</h3>
          
          <div style={{ background: '#2ea04315', borderLeft: '4px solid #2ea043', padding: '15px', borderRadius: '4px', marginBottom: '20px', display: 'flex', gap: '10px' }}>
            <Lightbulb size={20} color="#3fb950" />
            <div>
              <strong style={{ color: '#c9d1d9', display: 'block', marginBottom: '5px' }}>Recomendación principal</strong>
              <p style={{ color: '#8b949e', margin: 0, fontSize: '14px' }}>{feedbackText}</p>
            </div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px', color: '#c9d1d9', fontSize: '14px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <CheckCircle2 size={18} color="#58a6ff" />
              <span>{completedCheckpoints > 0 ? `Has completado ${completedCheckpoints} checkpoint(s).` : 'Aún no tienes checkpoints completados.'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <AlertCircle size={18} color="#ff7b72" />
              <span>{pendingCheckpoints > 0 ? `Tienes ${pendingCheckpoints} checkpoint(s) pendiente(s).` : 'No tienes checkpoints pendientes.'}</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <ListChecks size={18} color="#d2a8ff" />
              <span>Módulo sugerido: {cleanTitle(currentModule?.titulo || 'Ruta de aprendizaje')}</span>
            </div>
          </div>
        </article>

        {/* PANEL DERECHO: Indicadores */}
        <article className="report-panel" style={{ background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', margin: '0 0 20px 0', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>Seguimiento Formativo</h3>
          <div className="report-indicators">
            <IndicatorRow title="Avance de ruta" value={generalPercent} description="Progreso acumulado en los módulos." />
            <IndicatorRow title="Checkpoints" value={checkpointPercent} description="Evidencias prácticas completadas." />
            <IndicatorRow title="Continuidad" value={continuityPercent} description="Módulos iniciados por el estudiante." />
            <IndicatorRow title="Cierre de sesión" value={surveyPercent} description="Encuestas completadas." />
          </div>
        </article>
      </div>

      {/* PLAN SUGERIDO Y LISTA DE MÓDULOS */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '20px' }}>
        <section className="report-next-card" style={{ background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', margin: '0 0 20px 0', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>Plan Sugerido</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <NextStep number="1" title="Revisar teoría" description="Lee el propósito del módulo antes de ejecutar comandos." />
            <NextStep number="2" title="Ejecutar práctica" description="Usa el laboratorio local y guarda la evidencia generada." />
            <NextStep number="3" title="Validar checkpoints" description="Asegúrate de enviar las respuestas para que el docente las evalúe." />
          </div>
        </section>

        <section className="report-panel" style={{ background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', margin: '0 0 20px 0', borderBottom: '1px solid #30363d', paddingBottom: '10px' }}>Detalle por módulo</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            {modules.map((module) => (
              <ModuleResultItem key={module.id} module={module} />
            ))}
          </div>
        </section>
      </div>

    </div>
  );
}