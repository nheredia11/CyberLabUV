import { Clipboard, Play, RotateCcw, Square, TerminalSquare } from 'lucide-react';
import { useMemo, useState } from 'react';
import { api } from '../lib/api.js';

const scenarios = [
  { id: 'recon', title: 'Reconocimiento de red', command: 'bash scripts/run-scenario.sh recon', commands: ['nmap -sV 10.10.10.20', 'curl http://localhost:8081'] },
  { id: 'auth_http', title: 'Autenticación HTTP débil', command: 'bash scripts/run-scenario.sh auth_http', commands: ['curl -i http://localhost:8082/login', 'hydra -l student -P wordlists/demo.txt localhost http-post-form'] },
  { id: 'webapp', title: 'Aplicación web OWASP', command: 'bash scripts/run-scenario.sh webapp', commands: ["curl 'http://localhost:8083/search?q=test'", "curl 'http://localhost:8083/item?id=1'"] },
];

export default function Practice() {
  const [scenario, setScenario] = useState('auth_http');
  const [log, setLog] = useState('Selecciona una acción para registrar o ejecutar un escenario.');
  const [terminalOutput, setTerminalOutput] = useState('Terminal guiada lista. Usa comandos sugeridos para generar evidencia reproducible.');
  const [command, setCommand] = useState('curl -i http://localhost:8082/login');
  const selected = useMemo(() => scenarios.find(s => s.id === scenario), [scenario]);
  const execute = async (action) => {
    const res = await api.scenarioAction({ user_id: 'ana', scenario_id: scenario, action });
    setLog(`[${res.status}] ${res.message}`);
  };
  const runCommand = async (cmd = command) => {
    const res = await api.terminal({ user_id: 'ana', scenario_id: scenario, command: cmd });
    setCommand(res.command);
    setTerminalOutput(`$ ${res.command}\n[${res.status}]\n${res.output}`);
  };
  return <div className="grid grid-2">
    <div className="local-panel">
      <h2>Aplicación de simulación local</h2><p>Entorno Docker controlado + terminal guiada segura</p>
      <select value={scenario} onChange={e => { const s = scenarios.find(item => item.id === e.target.value); setScenario(e.target.value); setCommand(s.commands[0]); }}>
        {scenarios.map(s => <option key={s.id} value={s.id}>{s.title}</option>)}
      </select>
      <div className="grid grid-3" style={{marginTop:16}}>
        <button className="btn" onClick={() => execute('start')}><Play size={16}/>Iniciar</button>
        <button className="btn secondary" onClick={() => execute('reset')}><RotateCcw size={16}/>Reiniciar</button>
        <button className="btn secondary" onClick={() => execute('stop')}><Square size={16}/>Detener</button>
      </div>
      <h3><TerminalSquare size={18}/> Terminal / Evidencia</h3>
      <div className="terminal small">$ {selected.command}\n{log}</div>
      <div className="terminal-box">
        <label>Comando guiado</label>
        <div className="command-row"><input value={command} onChange={e => setCommand(e.target.value)}/><button className="btn" onClick={() => runCommand()}><TerminalSquare size={16}/>Ejecutar</button></div>
        <div className="quick-commands">{selected.commands.map(c => <button className="btn ghost" key={c} onClick={() => runCommand(c)}><Clipboard size={14}/>{c}</button>)}</div>
        <div className="terminal">{terminalOutput}</div>
      </div>
    </div>
    <div className="card">
      <h2>Estado del laboratorio</h2>
      <p><span className="badge">Listo para práctica</span></p>
      <div className="checkpoint"><Play/><div><strong>Primer escenario demostrable</strong><p className="muted">Autenticación HTTP débil permite mostrar inicio, terminal, evidencia y checkpoint.</p></div></div>
      <div className="checkpoint"><RotateCcw/><div><strong>Reproducible</strong><p className="muted">Cada acción queda registrada para analítica docente.</p></div></div>
      <div className="checkpoint"><TerminalSquare/><div><strong>Seguro por diseño</strong><p className="muted">La terminal sólo acepta comandos permitidos para evitar acciones fuera del laboratorio.</p></div></div>
    </div>
  </div>;
}
