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
import { ProgressBar } from '../components/Cards.jsx';

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
  if (percent >= 85) return { label: 'Alto', className: 'high' };
  if (percent >= 50) return { label: 'En progreso', className: 'mid' };
  if (percent > 0) return { label: 'Inicial', className: 'low' };
  return { label: 'Sin iniciar', className: 'empty' };
}

function ResultMetric({ icon: Icon, label, value, detail }) {
  return (
    <article className="report-metric">
      <span>
        <Icon size={20} />
      </span>

      <div>
        <strong>{value}</strong>
        <small>{label}</small>
        {detail && <em>{detail}</em>}
      </div>
    </article>
  );
}

function IndicatorRow({ title, value, description }) {
  const percent = clamp(value);
  const level = getLevel(percent);

  return (
    <div className="report-indicator-row">
      <div className="report-indicator-head">
        <div>
          <strong>{title}</strong>
          <small>{description}</small>
        </div>

        <span className={`report-level ${level.className}`}>
          {level.label}
        </span>
      </div>

      <ProgressBar value={percent} />

      <div className="report-indicator-percent">
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
    <article className="report-module-item">
      <div className="report-module-main">
        <div>
          <strong>{cleanTitle(module.titulo)}</strong>
          <small>{completed}/{total} checkpoints</small>
        </div>

        <span className={`report-level ${level.className}`}>
          {level.label}
        </span>
      </div>

      <ProgressBar value={percent} />

      <div className="report-module-foot">
        <span>{percent}% completado</span>
        <span>
          {module.progress?.survey_completed ? 'Encuesta realizada' : 'Encuesta pendiente'}
        </span>
      </div>
    </article>
  );
}

function NextStep({ number, title, description }) {
  return (
    <article className="report-next-step">
      <span>{number}</span>

      <div>
        <strong>{title}</strong>
        <p>{description}</p>
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
      <div className="results-report-page">
        <section className="results-report-loading">
          <div className="results-report-loader" />
          <div>
            <h3>Cargando resultados...</h3>
            <p>Estamos preparando tu retroalimentación.</p>
          </div>
        </section>
      </div>
    );
  }

  return (
    <div className="results-report-page">
      <section className="results-report-header">
        <div>
          <span className="report-chip">
            <FileText size={15} />
            Informe formativo
          </span>

          <h2>Resultados de {studentName}</h2>

          <p>
            Resumen de desempeño, evidencias y recomendaciones para continuar la ruta.
          </p>
        </div>

        <div className="results-report-actions">
          <button className="report-button secondary" onClick={() => setView?.('route')}>
            <Target size={17} />
            Continuar ruta
          </button>

          <button className="report-button primary" onClick={() => setView?.('practice')}>
            <RefreshCw size={17} />
            Ir al laboratorio
          </button>

          <button className="report-button ghost" onClick={() => window.print()}>
            <Download size={17} />
            Exportar
          </button>
        </div>
      </section>

      <section className="report-summary-card">
        <div className="report-summary-main">
          <span className={`report-level ${level.className}`}>
            {level.label}
          </span>

          <h3>{feedbackTitle}</h3>

          <p>{feedbackText}</p>
        </div>

        <div className="report-score-box">
          <strong>{generalPercent}%</strong>
          <span>avance general</span>
          <ProgressBar value={generalPercent} />
          <small>{completedModules}/{totalModules} módulos completados</small>
        </div>
      </section>

      <section className="report-metrics-grid">
        <ResultMetric
          icon={BookOpen}
          value={`${completedModules}/${totalModules}`}
          label="Módulos"
          detail="avance de la ruta"
        />

        <ResultMetric
          icon={ClipboardCheck}
          value={`${completedCheckpoints}/${totalCheckpoints}`}
          label="Checkpoints"
          detail="evidencias validadas"
        />

        <ResultMetric
          icon={Award}
          value={data?.badges || 0}
          label="Insignias"
          detail="logros obtenidos"
        />

        <ResultMetric
          icon={TrendingUp}
          value={data?.points || 0}
          label="Puntos"
          detail="acumulados"
        />
      </section>

      <section className="report-content-grid">
        <article className="report-panel">
          <div className="report-panel-title">
            <span className="report-chip">Lectura del desempeño</span>
            <h3>Retroalimentación</h3>
          </div>

          <div className="report-feedback-box">
            <Lightbulb size={23} />

            <div>
              <strong>Recomendación principal</strong>
              <p>{feedbackText}</p>
            </div>
          </div>

          <div className="report-feedback-list">
            <div>
              <CheckCircle2 size={18} />
              <span>
                {completedCheckpoints > 0
                  ? `Has completado ${completedCheckpoints} checkpoint(s).`
                  : 'Aún no tienes checkpoints completados.'}
              </span>
            </div>

            <div>
              <AlertCircle size={18} />
              <span>
                {pendingCheckpoints > 0
                  ? `Tienes ${pendingCheckpoints} checkpoint(s) pendiente(s).`
                  : 'No tienes checkpoints pendientes en la ruta actual.'}
              </span>
            </div>

            <div>
              <ListChecks size={18} />
              <span>
                Módulo sugerido: {cleanTitle(currentModule?.titulo || 'Ruta de aprendizaje')}.
              </span>
            </div>
          </div>
        </article>

        <article className="report-panel">
          <div className="report-panel-title">
            <span className="report-chip">Indicadores</span>
            <h3>Seguimiento formativo</h3>
          </div>

          <div className="report-indicators">
            <IndicatorRow
              title="Avance de ruta"
              value={generalPercent}
              description="Progreso acumulado en los módulos."
            />

            <IndicatorRow
              title="Checkpoints"
              value={checkpointPercent}
              description="Evidencias prácticas completadas."
            />

            <IndicatorRow
              title="Continuidad"
              value={continuityPercent}
              description="Módulos iniciados por el estudiante."
            />

            <IndicatorRow
              title="Cierre de sesión"
              value={surveyPercent}
              description="Encuestas o cierres completados."
            />
          </div>
        </article>
      </section>

      <section className="report-panel">
        <div className="report-panel-title horizontal">
          <div>
            <span className="report-chip">Escenarios</span>
            <h3>Detalle por módulo</h3>
          </div>

          <button className="report-link-button" onClick={() => setView?.('route')}>
            Ver ruta completa
          </button>
        </div>

        <div className="report-modules-list">
          {modules.map((module) => (
            <ModuleResultItem key={module.id} module={module} />
          ))}
        </div>
      </section>

      <section className="report-next-card">
        <div className="report-panel-title">
          <span className="report-chip">Próximos pasos</span>
          <h3>Plan sugerido</h3>
        </div>

        <div className="report-next-grid">
          <NextStep
            number="1"
            title="Revisar objetivo"
            description="Lee el propósito del módulo antes de ejecutar comandos."
          />

          <NextStep
            number="2"
            title="Ejecutar práctica"
            description="Usa el laboratorio local y guarda la evidencia generada."
          />

          <NextStep
            number="3"
            title="Cerrar checkpoints"
            description="Completa los puntos pendientes y revisa la retroalimentación."
          />
        </div>
      </section>
    </div>
  );
}