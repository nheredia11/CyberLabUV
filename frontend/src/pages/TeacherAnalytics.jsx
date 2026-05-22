import { useEffect, useState } from 'react';
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { api } from '../lib/api.js';

export default function TeacherAnalytics() {
  const [data, setData] = useState(null);
  useEffect(() => { api.analytics().then(setData); }, []);
  if (!data) return <div className="card">Cargando analíticas...</div>;
  return <div className="grid">
    <div className="card"><h2>Diseño de evaluación del curso</h2><p className="muted">Criterios sugeridos: reconocimiento/análisis, mitigación, persistencia/evidencia y reporte.</p>
      <div style={{width:'100%',height:280}}><ResponsiveContainer><BarChart data={data.modules}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="module_id"/><YAxis/><Tooltip/><Bar dataKey="avg_progress" name="Progreso promedio" /></BarChart></ResponsiveContainer></div>
    </div>
    <div className="grid grid-2">
      <div className="card"><h3>Seguimiento de módulos</h3><table className="table"><thead><tr><th>Módulo</th><th>Progreso</th></tr></thead><tbody>{data.modules.map(m => <tr key={m.module_id}><td>{m.title}</td><td>{m.avg_progress}%</td></tr>)}</tbody></table></div>
      <div className="card"><h3>Eventos recientes</h3>{data.scenario_events.length ? data.scenario_events.map((e, idx) => <p key={idx}><span className="badge">{e.status}</span> {e.scenario_id} · {e.action}</p>) : <p className="muted">Aún no hay eventos registrados.</p>}</div>
    </div>
  </div>;
}
