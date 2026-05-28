import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { AlertTriangle, CheckCircle2, ClipboardList, TerminalSquare, Users } from 'lucide-react';
import { Kpi } from '../components/Cards.jsx';
import { api } from '../lib/api.js';

export default function TeacherAnalytics() {
  const [data, setData] = useState(null);
  useEffect(() => { api.analytics().then(setData); }, []);
  if (!data) return <div className="card">Cargando analíticas...</div>;
  return <div className="grid">
    <div className="grid grid-4">
      <Kpi icon={Users} label="Progreso promedio" value={`${data.kpis.avg_course_progress}%`} />
      <Kpi icon={AlertTriangle} label="Alertas de refuerzo" value={data.kpis.students_at_risk} />
      <Kpi icon={CheckCircle2} label="Checkpoints cerrados" value={data.kpis.completed_checkpoints} />
      <Kpi icon={TerminalSquare} label="Comandos guiados" value={data.kpis.terminal_commands} />
    </div>
    <div className="card"><h2>Analíticas del docente</h2><p className="muted">Vista tipo dashboard con indicadores grandes, progreso por módulo y eventos técnicos.</p>
      <div style={{width:'100%',height:280}}><ResponsiveContainer><BarChart data={data.modules}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="module_id"/><YAxis/><Tooltip/><Bar dataKey="avg_progress" name="Progreso promedio" /></BarChart></ResponsiveContainer></div>
    </div>
    <div className="grid grid-2">
      <div className="card"><h3>Seguimiento de módulos</h3><table className="table"><thead><tr><th>Módulo</th><th>Nivel</th><th>Progreso</th></tr></thead><tbody>{data.modules.map(m => <tr key={m.module_id}><td>{m.title}</td><td>{m.level}</td><td>{m.avg_progress}%</td></tr>)}</tbody></table></div>
      <div className="card"><h3><ClipboardList size={18}/> Recomendaciones docentes</h3>{data.recommendations.map(r => <p key={r}>• {r}</p>)}<h3>Eventos recientes</h3>{data.scenario_events.length ? data.scenario_events.map((e, idx) => <p key={idx}><span className="badge">{e.status}</span> {e.scenario_id} · {e.action}</p>) : <p className="muted">Aún no hay eventos registrados.</p>}</div>
    </div>
  </div>;
}
