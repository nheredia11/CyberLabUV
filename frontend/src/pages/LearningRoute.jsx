import { useEffect, useMemo, useState } from "react";
import { marked } from "marked";
import DOMPurify from "dompurify";
import {
  getModuleById,
  getModuleFeedback,
  getModules,
  submitSurvey,
} from "../lib/api";
import Practice from "./Practice";
import SimulatedTerminal from "../components/SimulatedTerminal";

const PHASES = [
  { id: "theory", label: "Teoría", description: "Lectura guiada del módulo" },
  { id: "simulation", label: "Simulación", description: "Terminal segura sin Docker" },
  { id: "practice", label: "Práctica Real", description: "Escenario local controlado" },
  { id: "checkpoints", label: "Checkpoints", description: "Registro de evidencias" },
  { id: "survey", label: "Evaluación", description: "Encuesta y cierre" },
];

function resolveUserId(user) {
  const storedUser = localStorage.getItem("cyberlab_user");
  if (user?.id) return user.id;
  if (user?.email) return user.email;
  if (storedUser) {
    try {
      const parsed = JSON.parse(storedUser);
      return parsed?.id || parsed?.email || "demo-student";
    } catch {
      return "demo-student";
    }
  }
  return "demo-student";
}

function getModuleIdFromProps(props) {
  return (
    props.moduleId ||
    props.selectedModuleId ||
    props.currentModuleId ||
    props.module?.id ||
    props.module?.module_id ||
    "S02"
  );
}

function normalizeModule(moduleData) {
  if (!moduleData) return null;
  return {
    ...moduleData,
    id: moduleData.id || moduleData.module_id || "S02",
    title: moduleData.titulo || moduleData.title || moduleData.name || "Módulo CyberLab",
    description: moduleData.descripcion || moduleData.description || "Módulo académico de ciberseguridad.",
    objectives: moduleData.objetivos || moduleData.objectives || [],
    checkpoints: moduleData.checkpoints || moduleData.checkpoint_list || [],
    survey: moduleData.survey || moduleData.questions || [],
    theory: moduleData.theory_markdown || moduleData.theory || moduleData.content || "",
    feedback: moduleData.feedback || null,
    progress: moduleData.progress || null,
  };
}

function getQuestionDefault(question) {
  if (question.tipo === "likert_1_5" || question.type === "likert_1_5") {
    return "5";
  }
  return "";
}

export default function LearningRoute(props) {
  const { user, onBack, onNavigate } = props;
  const userId = resolveUserId(user);
  const initialModuleId = getModuleIdFromProps(props);

  const [moduleId, setModuleId] = useState(initialModuleId);
  const [modules, setModules] = useState([]);
  const [moduleRaw, setModuleRaw] = useState(props.module || null);
  const [activePhase, setActivePhase] = useState("theory");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [completedCheckpoints, setCompletedCheckpoints] = useState({});
  const [surveyAnswers, setSurveyAnswers] = useState({});
  const [savingSurvey, setSavingSurvey] = useState(false);
  const [surveyMessage, setSurveyMessage] = useState("");
  const [feedback, setFeedback] = useState(null);

  // Estados para manejo de Checkpoints y Evidencias
  const [answers, setAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [checkpointMessage, setCheckpointMessage] = useState({ text: "", type: "" });

  const moduleData = useMemo(() => normalizeModule(moduleRaw), [moduleRaw]);

  const theoryHtml = useMemo(() => {
    const source = moduleData?.theory || "";
    if (!source.trim()) {
      return DOMPurify.sanitize("<p>No hay contenido teórico disponible para este módulo.</p>");
    }
    return DOMPurify.sanitize(marked.parse(source));
  }, [moduleData]);

  useEffect(() => {
    setModuleId(initialModuleId);
  }, [initialModuleId]);

  useEffect(() => {
    async function loadCatalog() {
      try {
        const data = await getModules();
        setModules(Array.isArray(data) ? data : []);
      } catch {
        setModules([]);
      }
    }
    loadCatalog();
  }, []);

  useEffect(() => {
    async function loadModule() {
      try {
        setLoading(true);
        setError("");
        const data = await getModuleById(moduleId, userId);
        setModuleRaw(data);

        const normalized = normalizeModule(data);
        const initialCompleted = {};

        (normalized?.checkpoints || []).forEach((checkpoint) => {
          const isCompleted = checkpoint.completed || checkpoint.status === "completed" || false;
          initialCompleted[checkpoint.id] = Boolean(isCompleted);
        });

        setCompletedCheckpoints(initialCompleted);

        const initialSurvey = {};
        (normalized?.survey || []).forEach((question) => {
          initialSurvey[question.id] = getQuestionDefault(question);
        });
        setSurveyAnswers(initialSurvey);

        try {
          const feedbackData = await getModuleFeedback(normalized.id, userId);
          setFeedback(feedbackData);
        } catch {
          setFeedback(normalized.feedback || null);
        }
      } catch (loadError) {
        setError(loadError.message || "No fue posible cargar el módulo.");
      } finally {
        setLoading(false);
      }
    }
    loadModule();
  }, [moduleId, userId]);

  function handleBack() {
    if (onBack) return onBack();
    if (onNavigate) onNavigate("dashboard");
  }

  function handleModuleChange(event) {
    const nextModuleId = event.target.value;
    setModuleId(nextModuleId);
    setActivePhase("theory");
    setCheckpointMessage({ text: "", type: "" });
    setSurveyMessage("");
    if (props.onModuleChange) props.onModuleChange(nextModuleId);
  }

  const handleSubmitCheckpoints = async () => {
    setIsSubmitting(true);
    setCheckpointMessage({ text: "Guardando evidencias...", type: "info" });
    try {
      const response = await fetch("http://localhost:8000/api/progress/checkpoints", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-cyberlab-token": "dev-token-secret"
        },
        body: JSON.stringify({
          module_id: moduleData?.id || "S01",
          student_id: userId,
          answers: answers
        })
      });

      if (response.ok) {
        setCheckpointMessage({ text: "¡Evidencias evaluadas y registradas correctamente!", type: "success" });
        setTimeout(() => setActivePhase("survey"), 1500); // Salto automático tras 1.5s
      } else {
        setCheckpointMessage({ text: "Error de conexión al guardar las evidencias.", type: "error" });
      }
    } catch (error) {
      console.error("Error al enviar checkpoints:", error);
      setCheckpointMessage({ text: "El backend no responde. Verifica que Docker y FastAPI estén corriendo.", type: "error" });
    } finally {
      setIsSubmitting(false);
    }
  };

  async function handleSubmitSurvey() {
    try {
      setSavingSurvey(true);
      setSurveyMessage("");
      const numericValues = Object.values(surveyAnswers).map(Number).filter((val) => !Number.isNaN(val));
      const rating = numericValues.length > 0 ? numericValues.reduce((tot, val) => tot + val, 0) / numericValues.length : null;

      await submitSurvey(moduleData.id, {
        user_id: userId,
        student_id: userId,
        module_id: moduleData.id,
        answers: surveyAnswers,
        rating,
        comments: surveyAnswers.comments || "",
      });
      setSurveyMessage("✅ Encuesta guardada correctamente. ¡Gracias por tu retroalimentación!");
    } catch (saveError) {
      setSurveyMessage(`❌ No se pudo guardar la encuesta: ${saveError.message}`);
    } finally {
      setSavingSurvey(false);
    }
  }

  const completedCount = Object.values(completedCheckpoints).filter(Boolean).length;
  const totalCheckpoints = moduleData?.checkpoints?.length || 0;
  const progressPercent = totalCheckpoints > 0 ? Math.round((completedCount / totalCheckpoints) * 100) : 0;

  if (loading && !moduleData) {
    return (
      <main className="learning-route-page">
        <section className="learning-loading">
          <span className="eyebrow">CyberLab</span>
          <h2>Cargando módulo...</h2>
          <p>Estamos preparando la ruta de aprendizaje.</p>
        </section>
      </main>
    );
  }

  if (error && !moduleData) {
    return (
      <main className="learning-route-page">
        <section className="learning-loading">
          <span className="eyebrow">Error</span>
          <h2>No se pudo cargar el módulo</h2>
          <p>{error}</p>
          <button type="button" onClick={handleBack}>Volver</button>
        </section>
      </main>
    );
  }

  return (
    <main className="learning-route-page">
      <section className="learning-route-hero">
        <div>
          <span className="eyebrow">Ruta de aprendizaje</span>
          <h1>{moduleData?.id} · {moduleData?.title}</h1>
          <p>{moduleData?.description}</p>
          <div className="learning-route-actions">
            <button type="button" onClick={handleBack} className="secondary-button">
              Volver al tablero
            </button>
          </div>
        </div>

        <aside className="learning-route-summary">
          <label>
            Módulo
            <select value={moduleId} onChange={handleModuleChange}>
              {modules.length === 0 && <option value={moduleId}>{moduleId}</option>}
              {modules.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.id} · {item.titulo || item.title}
                </option>
              ))}
            </select>
          </label>
          <div className="summary-kpi"><span>Estudiante</span><strong>{userId}</strong></div>
          <div className="summary-kpi"><span>Checkpoints</span><strong>{completedCount}/{totalCheckpoints}</strong></div>
          <div className="summary-kpi"><span>Progreso</span><strong>{progressPercent}%</strong></div>
        </aside>
      </section>

      <nav className="learning-phase-nav">
        {PHASES.map((phase) => (
          <button
            key={phase.id}
            type="button"
            className={activePhase === phase.id ? "active" : ""}
            onClick={() => setActivePhase(phase.id)}
          >
            <strong>{phase.label}</strong>
            <span>{phase.description}</span>
          </button>
        ))}
      </nav>

      {activePhase === "simulation" && (
        <section className="learning-panel">
          <div className="section-heading">
            <span className="eyebrow">Simulación Ligera WebAssembly / Mock</span>
            <h2>Entorno de pruebas en navegador</h2>
            <p>
              Practica los comandos requeridos directamente en tu navegador sin consumir 
              recursos de tu computadora. Cuando domines la sintaxis, pasa a la 
              "Práctica Real" para interactuar con los contenedores.
            </p>
          </div>
          <SimulatedTerminal scenarioId={moduleData?.id} />
        </section>
      )}

      {activePhase === "theory" && (
        <section className="learning-panel">
          <div className="section-heading">
            <span className="eyebrow">Teoría del módulo</span>
            <h2>{moduleData?.title || "Contenido teórico"}</h2>
            <p>Lee detenidamente los fundamentos antes de proceder a la práctica.</p>
          </div>
          <article className="markdown-content" dangerouslySetInnerHTML={{ __html: theoryHtml }} />
        </section>
      )}

      {activePhase === "practice" && (
        <section className="learning-panel">
          <div className="section-heading">
            <span className="eyebrow">Laboratorio local</span>
            <h2>Práctica guiada</h2>
            <p>Inicia el escenario, revisa el laboratorio y ejecuta comandos permitidos desde la terminal guiada.</p>
          </div>
          <Practice user={user} moduleId={moduleData?.id} moduleData={moduleData} />
        </section>
      )}

      {activePhase === "checkpoints" && (
        <section className="learning-panel">
          <div className="section-heading">
            <span className="eyebrow">Validación de Conocimiento</span>
            <h2>Registro de Evidencias (Flags)</h2>
            <p>Ingresa los resultados obtenidos durante tu Práctica Real. Esto nos ayudará a evaluar cualitativamente tu progreso.</p>
          </div>
          
          <div className="checkpoints-form" style={{ background: '#161b22', padding: '24px', borderRadius: '8px', marginTop: '20px', border: '1px solid #30363d' }}>
            {moduleData?.checkpoints ? (
              moduleData.checkpoints.map((cp, idx) => (
                <div key={idx} style={{ marginBottom: '20px' }}>
                  <label style={{ display: 'block', color: '#c9d1d9', fontWeight: 'bold', marginBottom: '8px' }}>
                    🚩 Pregunta {idx + 1}: {cp.question || cp.pregunta || `Checkpoint ${idx + 1}`}
                  </label>
                  <input 
                    type="text" 
                    placeholder="Escribe tu respuesta o flag aquí..." 
                    value={answers[cp.id || idx] || ""}
                    onChange={(e) => setAnswers({...answers, [cp.id || idx]: e.target.value})}
                    style={{ width: '100%', padding: '12px', borderRadius: '6px', border: '1px solid #30363d', background: '#0d1117', color: '#58a6ff', fontFamily: 'monospace', outline: 'none' }} 
                  />
                </div>
              ))
            ) : (
              <p style={{ color: '#8b949e' }}>No hay checkpoints configurados para este escenario.</p>
            )}
            
            {checkpointMessage.text && (
              <div style={{ marginBottom: '15px', padding: '10px', borderRadius: '4px', background: checkpointMessage.type === 'error' ? '#f8514920' : '#2ea04320', color: checkpointMessage.type === 'error' ? '#ff7b72' : '#3fb950', border: `1px solid ${checkpointMessage.type === 'error' ? '#f85149' : '#2ea043'}` }}>
                {checkpointMessage.text}
              </div>
            )}

            <button 
              type="button"
              disabled={isSubmitting}
              style={{ padding: '12px 24px', background: isSubmitting ? '#555' : '#238636', color: '#ffffff', fontWeight: 'bold', border: 'none', borderRadius: '6px', cursor: isSubmitting ? 'not-allowed' : 'pointer', transition: '0.2s' }}
              onClick={handleSubmitCheckpoints}
            >
              {isSubmitting ? "Enviando evidencias..." : "Enviar Evidencias"}
            </button>
          </div>
        </section>
      )}

      {activePhase === "survey" && (
        <section className="learning-panel">
          <div className="section-heading">
            <span className="eyebrow">Cierre y retroalimentación</span>
            <h2>Encuesta del módulo</h2>
            <p>Evalúa la claridad y utilidad del escenario para ayudarnos a mejorar la calidad de los laboratorios.</p>
          </div>

          {surveyMessage && (
            <div style={{ marginBottom: '20px', padding: '12px', borderRadius: '6px', background: surveyMessage.includes('❌') ? '#f8514920' : '#2ea04320', color: surveyMessage.includes('❌') ? '#ff7b72' : '#3fb950', border: `1px solid ${surveyMessage.includes('❌') ? '#f85149' : '#2ea043'}` }}>
              {surveyMessage}
            </div>
          )}

          <div className="survey-grid" style={{ display: 'grid', gap: '15px', marginBottom: '20px' }}>
            {(moduleData?.survey || []).map((question) => {
              const type = question.tipo || question.type;
              return (
                <div key={question.id} style={{ background: '#161b22', padding: '15px', borderRadius: '6px', border: '1px solid #30363d' }}>
                  <span style={{ display: 'block', marginBottom: '10px', color: '#c9d1d9', fontWeight: 'bold' }}>{question.pregunta || question.question}</span>
                  {type === "likert_1_5" ? (
                    <select
                      value={surveyAnswers[question.id] || "5"}
                      onChange={(e) => setSurveyAnswers({ ...surveyAnswers, [question.id]: e.target.value })}
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d' }}
                    >
                      <option value="5">5 · Totalmente de acuerdo</option>
                      <option value="4">4 · De acuerdo</option>
                      <option value="3">3 · Neutral</option>
                      <option value="2">2 · En desacuerdo</option>
                      <option value="1">1 · Totalmente en desacuerdo</option>
                    </select>
                  ) : (
                    <textarea
                      value={surveyAnswers[question.id] || ""}
                      onChange={(e) => setSurveyAnswers({ ...surveyAnswers, [question.id]: e.target.value })}
                      placeholder="Escribe tu respuesta..."
                      style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d', minHeight: '60px' }}
                    />
                  )}
                </div>
              );
            })}
            
            <div style={{ background: '#161b22', padding: '15px', borderRadius: '6px', border: '1px solid #30363d' }}>
              <span style={{ display: 'block', marginBottom: '10px', color: '#c9d1d9', fontWeight: 'bold' }}>Comentario general</span>
              <textarea
                value={surveyAnswers.comments || ""}
                onChange={(e) => setSurveyAnswers({ ...surveyAnswers, comments: e.target.value })}
                placeholder="Describe qué fue claro, qué fue difícil o qué reforzarías."
                style={{ width: '100%', padding: '8px', borderRadius: '4px', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d', minHeight: '80px' }}
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleSubmitSurvey}
            disabled={savingSurvey}
            style={{ padding: '12px 24px', background: savingSurvey ? '#555' : '#1f6feb', color: '#ffffff', fontWeight: 'bold', border: 'none', borderRadius: '6px', cursor: savingSurvey ? 'not-allowed' : 'pointer' }}
          >
            {savingSurvey ? "Guardando encuesta..." : "Guardar encuesta"}
          </button>

          {/* Renderizado limpio de Retroalimentación del Docente */}
          {feedback && Object.keys(feedback).length > 0 && (
            <article style={{ marginTop: '30px', padding: '20px', background: '#23863615', borderLeft: '4px solid #2ea043', borderRadius: '4px' }}>
              <h3 style={{ color: '#3fb950', marginTop: 0, display: 'flex', alignItems: 'center', gap: '8px' }}>
                👨‍🏫 Retroalimentación del Docente
              </h3>
              <p style={{ color: '#c9d1d9', lineHeight: '1.6', margin: 0 }}>
                {feedback.message || feedback.feedback || "Revisa tus evidencias en el panel de resultados."}
              </p>
            </article>
          )}
        </section>
      )}
    </main>
  );
}