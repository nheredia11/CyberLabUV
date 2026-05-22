import { Play, RotateCcw, Square, TerminalSquare } from 'lucide-react';
import { useState } from 'react';
import { api } from '../lib/api.js';

const scenarios = [
  { id: 'recon', title: 'Reconocimiento de red', command: 'bash scripts/run-scenario.sh recon' },
  { id: 'auth_http', title: 'Autenticación HTTP débil', command: 'bash scripts/run-scenario.sh auth_http' },
  { id: 'webapp', title: 'Aplicación web OWASP', command: 'bash scripts/run-scenario.sh webapp' },
];

export default function Practice() {
  const [scenario, setScenario] = useState('auth_http');
  const [log, setLog] = useState('Selecciona una acción para registrar o ejecutar un escenario.');
  const execute = async (action) => {
    const res = await api.scenarioAction({ user_id: 'ana', scenario_id: scenario, action });
    setLog(`[${res.status}] ${res.message}`);
  };
  const selected = scenarios.find(s => s.id === scenario);
  return <div className="grid grid-2">
    <div className="local-panel">
      <h2>Aplicación de simulación local</h2><p>Entorno Docker controlado</p>
      <select value={scenario} onChange={e => setScenario(e.target.value)}>{scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}</select>
      <div className="grid grid-3" style={{marginTop:16}}>
        <button className="btn" onClick={() => execute('start')}><Play size={16}/>Iniciar</button>
        <button className="btn secondary" onClick={() => execute('reset')}><RotateCcw size={16}/>Reiniciar</button>
        <button className="btn secondary" onClick={() => execute('stop')}><Square size={16}/>Detener</button>
      </div>
      <h3><TerminalSquare size={18}/> Terminal / Evidencia</h3><div className="terminal">$ {selected.command}\n{log}</div>
    </div>
    <div className="card">
      <h2>Estado del laboratorio</h2>
      <p><span className="badge">Listo para práctica</span></p>
      <div className="checkpoint"><Play/><div><strong>Docker Engine</strong><p className="muted">Validado por scripts/check-requirements.sh</p></div></div>
      <div className="checkpoint"><RotateCcw/><div><strong>Docker Compose</strong><p className="muted">Cada escenario se levanta de forma independiente.</p></div></div>
      <div className="checkpoint"><TerminalSquare/><div><strong>Sync automática</strong><p className="muted">La plataforma registra eventos, checkpoints y encuestas en SQLite.</p></div></div>
    </div>
  </div>;
}
