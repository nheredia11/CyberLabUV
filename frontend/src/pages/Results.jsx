import { Lightbulb, Medal, Target } from 'lucide-react';
import { ProgressBar } from '../components/Cards.jsx';

export default function Results({ data }) {
  if (!data) return <div className="card">Cargando resultados...</div>;
  const current = data.modules.find(m => m.progress.percent < 100) || data.modules[0];
  return <div className="grid grid-2">
    <div className="card">
      <h2>Resultados de la práctica</h2><p className="muted">Ruta de aprendizaje / Resultados / {current?.titulo}</p>
      <div className="card soft"><h3>Retroalimentación para Ana</h3><p>Buen trabajo. Revisa los aspectos por reforzar para cerrar la práctica con evidencia completa.</p></div>
      <h3>Fortalezas</h3><div className="checkpoint"><Target/><div>Identificaste checkpoints completados y registraste avance parcial.</div></div>
      <div className="checkpoint"><Medal/><div>Persistencia activa en SQLite para resultados y encuestas.</div></div>
      <h3>Aspectos por reforzar</h3><div className="checkpoint"><Lightbulb/><div>Completar encuestas post-sesión y documentar comandos usados en el laboratorio.</div></div>
    </div>
    <div className="card">
      <h3>Mi desempeño</h3>{data.modules.map(m => <div key={m.id} style={{marginBottom:16}}><strong>{m.id} · {m.titulo}</strong><ProgressBar value={m.progress.percent}/><small>{m.progress.percent}% · {m.progress.completed_checkpoints}/{m.progress.total_checkpoints} checkpoints</small></div>)}
      <div className="card soft"><strong>Sugerencias</strong><p>Intenta aumentar el nivel de autonomía en el manejo de Docker, logs y evidencias técnicas.</p></div>
    </div>
  </div>;
}
