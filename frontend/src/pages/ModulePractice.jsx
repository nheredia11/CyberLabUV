import { useState, useEffect } from 'react';
import {
  CheckCircle2,
  Lightbulb,
  TerminalSquare,
  ArrowRight,
} from 'lucide-react';
import { ProgressBar } from '../components/Cards.jsx';
import { api } from '../lib/api.js';

export default function ModulePractice({ moduleId, userId, onBack }) {
  const [module, setModule] = useState(null);
  const [progress, setProgress] = useState(0);
  const [completedCheckpoints, setCompletedCheckpoints] = useState([]);
  const [feedback, setFeedback] = useState(null);

  useEffect(() => {
    async function loadModule() {
      const data = await api.getModule(moduleId, userId);
      setModule(data.module);
      setProgress(data.module.progress?.percent || 0);
      setCompletedCheckpoints(data.module.progress?.completed_checkpoints || []);
      setFeedback(data.module.feedback || null);
    }

    loadModule();
  }, [moduleId, userId]);

  function toggleCheckpoint(checkpointId) {
    let updated = [...completedCheckpoints];
    if (updated.includes(checkpointId)) {
      updated = updated.filter((id) => id !== checkpointId);
    } else {
      updated.push(checkpointId);
    }
    setCompletedCheckpoints(updated);
    setProgress(Math.round((updated.length / module.totalCheckpoints) * 100));
    setFeedback(updated.length === module.totalCheckpoints ? '¡Felicidades! Módulo completo.' : null);
  }

  if (!module) return <p>Cargando módulo...</p>;

  return (
    <div className="module-practice-page">
      <button className="btn ghost" onClick={onBack}>
        ← Volver al dashboard
      </button>

      <h1>{module.titulo}</h1>
      <p>{module.descripcion}</p>

      <section className="module-objectives">
        <h3>Objetivos</h3>
        <ul>
          {module.objetivos.map((obj) => (
            <li key={obj}>{obj}</li>
          ))}
        </ul>
      </section>

      <section className="module-lab">
        <h3>Laboratorio local</h3>
        <p>
          Ejecuta los pasos del laboratorio local de forma guiada. Cada checkpoint
          se actualizará automáticamente al completarlo.
        </p>
      </section>

      <section className="module-checkpoints">
        <h3>Checkpoints ({completedCheckpoints.length}/{module.totalCheckpoints})</h3>
        <ul>
          {module.checkpoints.map((cp) => (
            <li key={cp.id}>
              <button
                className={completedCheckpoints.includes(cp.id) ? 'done' : ''}
                onClick={() => toggleCheckpoint(cp.id)}
              >
                <CheckCircle2 size={16} />
                {cp.titulo}
              </button>
            </li>
          ))}
        </ul>
      </section>

      {feedback && (
        <section className="module-feedback">
          <Lightbulb size={18} />
          <strong>Feedback</strong>
          <p>{feedback}</p>
        </section>
      )}

      <ProgressBar value={progress} />

      <button className="btn primary full" onClick={onBack}>
        <ArrowRight size={16} /> Volver al dashboard
      </button>
    </div>
  );
}