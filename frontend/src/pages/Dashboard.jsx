import { Award, BookOpen, CheckCircle2, Flame, PlayCircle, Star } from 'lucide-react';
import { Kpi, ProgressBar } from '../components/Cards.jsx';

export default function Dashboard({ data, setView, setSelectedModule }) {
  if (!data) return <div className="card">Cargando dashboard...</div>;
  return <div className="grid">
    <div className="grid grid-4">
      <Kpi icon={BookOpen} label="Progreso general del curso" value={`${data.general_percent}%`} />
      <Kpi icon={CheckCircle2} label="Módulos completos" value={`${data.completed_modules}/${data.total_modules}`} />
      <Kpi icon={Award} label="Insignias obtenidas" value={data.badges} />
      <Kpi icon={Flame} label="Puntos totales" value={data.points} />
    </div>
    <div className="card">
      <h2>Tu ruta de aprendizaje</h2>
      <p className="muted">Completa teoría, práctica guiada, checkpoints y encuesta por cada módulo.</p>
      <div className="grid">
        {data.modules.map((m) => <div className="module-card card soft" key={m.id}>
          <div className="kpi-icon"><Star size={22}/></div>
          <div><strong>{m.titulo}</strong><p className="muted">{m.descripcion}</p><ProgressBar value={m.progress.percent}/><small>{m.progress.completed_checkpoints}/{m.progress.total_checkpoints} checkpoints · Encuesta {m.progress.survey_completed ? 'lista' : 'pendiente'}</small></div>
          <button className="btn" onClick={() => { setSelectedModule(m.id); setView('route'); }}><PlayCircle size={16}/>Ver módulo</button>
        </div>)}
      </div>
    </div>
    <div className="grid grid-3">
      <div className="card"><span className="badge">Nivel 3 · Explorador</span><h3>Próximo reto</h3><p>{data.current_module?.titulo}</p></div>
      <div className="card"><span className="badge">Racha de estudio</span><h3>5 días</h3><p className="muted">Mantén el ritmo para llegar a la validación con evidencias.</p></div>
      <div className="card"><span className="badge lock">Sugerencias</span><p>Revisa la teoría antes de entrar a la práctica local y guarda evidencia por checkpoint.</p></div>
    </div>
  </div>;
}
