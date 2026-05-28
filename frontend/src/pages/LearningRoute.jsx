import { Bot, CheckCircle2, FileText, Save, Send } from 'lucide-react';
import { useEffect, useState } from 'react';
import { api } from '../lib/api.js';
import { ProgressBar } from '../components/Cards.jsx';

function Markdown({ text }) {
  return <div className="markdown">{text.split('\n').map((line, idx) => line.startsWith('#') ? <h3 key={idx}>{line.replace(/^#+\s*/, '')}</h3> : line.trim().startsWith('-') ? <li key={idx}>{line.replace(/^[-*]\s*/, '')}</li> : <p key={idx}>{line}</p>)}</div>;
}

export default function LearningRoute({ selectedModule, setSelectedModule, refreshDashboard }) {
  const [modules, setModules] = useState([]);
  const [module, setModule] = useState(null);
  const [tab, setTab] = useState('theory');
  const [evidence, setEvidence] = useState({});
  const [answers, setAnswers] = useState({});
  useEffect(() => { api.modules().then(setModules); }, []);
  useEffect(() => { api.module(selectedModule).then(setModule); }, [selectedModule]);
  if (!module) return <div className="card">Cargando módulo...</div>;
  const progress = module.progress || { percent: 0 };
  const feedback = module.feedback;
  const submitCheckpoint = async (cp) => {
    await api.saveCheckpoint(module.id, { user_id: 'ana', checkpoint_id: cp.id, status: 'done', evidence: evidence[cp.id] || 'Confirmado desde interfaz web' });
    await refreshDashboard();
    const fresh = await api.module(module.id); setModule(fresh);
  };
  const submitSurvey = async () => { await api.saveSurvey(module.id, { user_id: 'ana', answers, rating: Number(answers.rating || 5), comments: answers.comments || '' }); await refreshDashboard(); const fresh = await api.module(module.id); setModule(fresh); alert('Encuesta guardada'); };
  return <div className="grid grid-2">
    <div className="card">
      <label className="muted">Módulo seleccionado</label>
      <select value={selectedModule} onChange={(e) => setSelectedModule(e.target.value)}>{modules.map(m => <option value={m.id} key={m.id}>{m.id} · {m.titulo}</option>)}</select>
      <h2>{module.titulo}</h2><p className="muted">{module.descripcion}</p><ProgressBar value={progress.percent || 0}/>
      <div className="feedback-card"><Bot/><div><strong>Retroalimentación adaptativa · {feedback?.level}</strong><p>{feedback?.message}</p></div></div>
      <div className="tabs"><button className={`tab ${tab==='theory'?'active':''}`} onClick={() => setTab('theory')}>Teoría</button><button className={`tab ${tab==='practice'?'active':''}`} onClick={() => setTab('practice')}>Práctica</button><button className={`tab ${tab==='survey'?'active':''}`} onClick={() => setTab('survey')}>Evaluación</button></div>
      {tab === 'theory' && <Markdown text={module.theory || 'Contenido teórico pendiente.'}/>} 
      {tab === 'practice' && <div>{module.checkpoints.map(cp => <div className="checkpoint" key={cp.id}><CheckCircle2 color="var(--accent)"/><div><strong>{cp.titulo}</strong><p className="muted">Evidencia esperada: {cp.evidencia}</p>{cp.tipo === 'texto' && <textarea placeholder="Describe tu evidencia..." value={evidence[cp.id] || ''} onChange={e => setEvidence({...evidence, [cp.id]: e.target.value})}/>}<button className="btn" onClick={() => submitCheckpoint(cp)}><Save size={16}/>Guardar checkpoint</button></div></div>)}</div>}
      {tab === 'survey' && <div className="grid">{module.survey.map(q => <label key={q.id}>{q.pregunta}{q.tipo.includes('likert') ? <select value={answers[q.id] || ''} onChange={e => setAnswers({...answers, [q.id]: e.target.value, rating: e.target.value})}><option value="">Seleccionar</option>{[1,2,3,4,5].map(n => <option key={n} value={n}>{n}</option>)}</select> : <textarea value={answers[q.id] || ''} onChange={e => setAnswers({...answers, [q.id]: e.target.value, comments: e.target.value})}/>}</label>)}<button className="btn" onClick={submitSurvey}><Send size={16}/>Enviar encuesta</button></div>}
    </div>
    <div className="card">
      <h3>Conexión con laboratorio local</h3><p className="muted">El módulo se conecta con el escenario Docker asignado, registra acciones y genera retroalimentación.</p>
      <div className="card soft"><FileText/> <strong>Objetivos</strong><ul>{(module.objetivos || []).map(o => <li key={o}>{o}</li>)}</ul></div>
      <div className="card soft"><strong>Siguientes acciones</strong>{feedback?.next_actions?.map(a => <p key={a}>• {a}</p>)}</div>
      <div className="card soft"><strong>Checkpoints pendientes</strong>{feedback?.missing_checkpoints?.length ? feedback.missing_checkpoints.map(cp => <p key={cp}>• {cp}</p>) : <p>Sin pendientes principales.</p>}</div>
    </div>
  </div>;
}
