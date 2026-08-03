import { useMemo, useState, useRef, useEffect } from "react";
import {
  runScenarioAction,
  runTerminalCommand,
} from "../lib/api";

const LAB_URLS = {
  M00: null,
  S01: "http://127.0.0.1:8083",
  S02: "http://127.0.0.1:8081",
  S03: "http://127.0.0.1:8084",
  S04: "http://127.0.0.1:8085",
  S05: "http://127.0.0.1:8086",
};

const SAFE_COMMANDS = {
  S01: [
    "nmap -sV recon-lab",
    "curl -I http://recon-lab:5000",
  ],
  S02: [
    "hydra -l estudiante -P wordlists/demo.txt localhost http-post-form",
    "curl -i http://127.0.0.1:8081/health",
  ],
  S03: [
    "curl 'http://web-owasp-lab/search?q=1%20OR%201=1'",
    "curl 'http://web-owasp-lab/search?q=test'",
    "curl 'http://web-owasp-lab/file?name=readme.txt'",
  ],
  S04: [
    "nmap -p 21,22 auth-services-lab",
    "hydra -l admin -P wordlists/fast.txt ssh://auth-services-lab",
  ],
  S05: [
    "arpspoof -i eth0 -t victima_ip puerta_enlace_ip",
    "tcpdump -i eth0 -n -A 'tcp port 80'",
  ],
};

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

function normalizeScenarioId(moduleId, moduleData) {
  const value =
    moduleData?.id ||
    moduleData?.module_id ||
    moduleId ||
    "S02";

  return String(value).toUpperCase();
}

function getActionLabel(action) {
  const labels = {
    start: "Iniciar escenario",
    status: "Consultar estado",
    reset: "Reiniciar escenario",
    stop: "Detener escenario",
  };

  return labels[action] || action;
}

export default function Practice({
  user,
  moduleId = "S02",
  moduleData = null,
  onScenarioEvent,
}) {
  const scenarioId = normalizeScenarioId(moduleId, moduleData);
  const userId = resolveUserId(user);
  const labUrl = LAB_URLS[scenarioId];

  const [selectedCommand, setSelectedCommand] = useState(
    SAFE_COMMANDS[scenarioId]?.[0] || ""
  );
  const [customCommand, setCustomCommand] = useState("");
  const [loadingAction, setLoadingAction] = useState("");
  const [loadingCommand, setLoadingCommand] = useState(false);
  
  // Refactorizamos la salida para que sea un historial limpio de terminal
  const [outputHistory, setOutputHistory] = useState([
    `[CyberLab OS] - Conectado como ${userId}`,
    "Escribe o selecciona un comando de la lista blanca para comenzar."
  ]);
  const consoleBottomRef = useRef(null);

  const commands = useMemo(() => {
    return SAFE_COMMANDS[scenarioId] || [];
  }, [scenarioId]);

  // Scroll automático hacia abajo en la consola
  useEffect(() => {
    consoleBottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [outputHistory]);

  const appendToConsole = (text, isCommand = false, isError = false) => {
    setOutputHistory(prev => {
      let newEntry = text;
      if (isCommand) newEntry = `\ncyberlab@student:~$ ${text}`;
      if (isError) newEntry = `[ERROR] ${text}`;
      return [...prev, newEntry];
    });
  };

  const clearConsole = () => {
    setOutputHistory(["Consola limpiada."]);
  };

  async function handleScenarioAction(action) {
    try {
      setLoadingAction(action);
      appendToConsole(`Iniciando acción del sistema: [${action}]...`);

      const response = await runScenarioAction({
        user_id: userId,
        scenario_id: scenarioId,
        action,
      });

      // Extraemos solo el mensaje o salida limpia
      const cleanOutput = response.stdout || response.message || response.stderr || "Acción completada sin salida en consola.";
      appendToConsole(cleanOutput);

      if (onScenarioEvent) {
        onScenarioEvent(response);
      }
    } catch (error) {
      appendToConsole(error.message, false, true);
    } finally {
      setLoadingAction("");
    }
  }

  async function handleTerminalCommand(commandValue) {
    const command = commandValue?.trim();

    if (!command) {
      appendToConsole("Debes seleccionar o escribir un comando.", false, true);
      return;
    }

    try {
      setLoadingCommand(true);
      appendToConsole(command, true); // Imprimir el comando que se acaba de lanzar

      const response = await runTerminalCommand({
        user_id: userId,
        scenario_id: scenarioId,
        command,
      });

      // Validar si el backend bloqueó el comando por la lista blanca
      if (response.allowed === false) {
         appendToConsole(`🔒 SEGURIDAD: ${response.message}`, false, true);
         return;
      }

      // Mostrar el stdout limpio de Docker (ej: la salida de nmap real)
      const cleanOutput = response.stdout || response.stderr || response.message || "Comando ejecutado sin salida.";
      appendToConsole(cleanOutput);

    } catch (error) {
      appendToConsole(`Error de ejecución: ${error.message}`, false, true);
    } finally {
      setLoadingCommand(false);
    }
  }

  if (!labUrl && scenarioId === "M00") {
    return (
      <section className="practice-shell">
        <div className="practice-hero">
          <span className="eyebrow">M00 · Inducción</span>
          <h2>Módulo sin laboratorio Docker</h2>
          <p>
            Este módulo corresponde a la inducción ética y académica. No requiere
            iniciar un contenedor porque su objetivo es explicar reglas, límites y
            uso responsable del simulador.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="practice-shell" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      <div className="practice-hero" style={{ background: '#161b22', padding: '24px', borderRadius: '8px', border: '1px solid #30363d' }}>
        <span className="eyebrow" style={{ color: '#8b949e', textTransform: 'uppercase', fontSize: '12px' }}>Práctica local controlada</span>
        <h2 style={{ color: '#c9d1d9', marginTop: '5px' }}>{scenarioId} · Laboratorio CyberLab</h2>
        <p style={{ color: '#8b949e' }}>
          Inicia el escenario Docker, revisa el objetivo y ejecuta comandos autorizados.
        </p>

        <div className="practice-meta-grid" style={{ display: 'flex', gap: '20px', marginTop: '15px' }}>
          <article style={{ background: '#0d1117', padding: '10px 15px', borderRadius: '6px', border: '1px solid #30363d', flex: 1 }}>
            <span style={{ fontSize: '12px', color: '#8b949e', display: 'block' }}>Usuario</span>
            <strong style={{ color: '#c9d1d9' }}>{userId}</strong>
          </article>
          <article style={{ background: '#0d1117', padding: '10px 15px', borderRadius: '6px', border: '1px solid #30363d', flex: 1 }}>
            <span style={{ fontSize: '12px', color: '#8b949e', display: 'block' }}>Escenario Activo</span>
            <strong style={{ color: '#58a6ff' }}>{scenarioId}</strong>
          </article>
        </div>
      </div>

      <div className="practice-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px' }}>
        
        {/* PANEL DE CONTROL DOCKER */}
        <article className="practice-card" style={{ background: '#161b22', padding: '20px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', marginBottom: '10px' }}>🐳 Control del Escenario</h3>
          <p style={{ color: '#8b949e', fontSize: '13px', marginBottom: '15px' }}>
            Gestiona el ciclo de vida de los contenedores Docker en tu entorno local.
          </p>

          <div className="practice-actions" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '15px' }}>
            {["start", "status", "reset", "stop"].map((action) => (
              <button
                key={action}
                type="button"
                style={{ 
                  padding: '10px', 
                  background: action === 'start' ? '#238636' : action === 'stop' ? '#da3633' : '#21262d', 
                  color: '#fff', 
                  border: '1px solid #30363d', 
                  borderRadius: '6px', 
                  cursor: loadingAction ? 'wait' : 'pointer',
                  fontWeight: 'bold',
                  opacity: loadingAction ? 0.7 : 1
                }}
                onClick={() => handleScenarioAction(action)}
                disabled={Boolean(loadingAction)}
              >
                {loadingAction === action ? "⏳" : getActionLabel(action)}
              </button>
            ))}
          </div>

          {labUrl && (
            <a
              className="open-lab-button"
              href={labUrl}
              target="_blank"
              rel="noreferrer"
              style={{ display: 'block', textAlign: 'center', padding: '10px', background: '#1f6feb', color: '#fff', textDecoration: 'none', borderRadius: '6px', fontWeight: 'bold' }}
            >
              🌐 Abrir aplicación vulnerable
            </a>
          )}
        </article>

        {/* PANEL DE COMANDOS */}
        <article className="practice-card" style={{ background: '#161b22', padding: '20px', borderRadius: '8px', border: '1px solid #30363d' }}>
          <h3 style={{ color: '#c9d1d9', marginBottom: '10px' }}>⌨️ Terminal Guiada</h3>
          <p style={{ color: '#8b949e', fontSize: '13px', marginBottom: '15px' }}>
            Ejecuta comandos de reconocimiento y explotación desde la máquina atacante.
          </p>

          <div style={{ marginBottom: '15px' }}>
            <label style={{ display: 'block', color: '#c9d1d9', fontSize: '13px', marginBottom: '5px' }}>Comando sugerido (Lista Blanca)</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <select
                value={selectedCommand}
                onChange={(event) => setSelectedCommand(event.target.value)}
                style={{ flex: 1, padding: '10px', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px' }}
              >
                {commands.length === 0 && <option value="">No hay comandos definidos</option>}
                {commands.map((command) => (
                  <option key={command} value={command}>{command}</option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => handleTerminalCommand(selectedCommand)}
                disabled={loadingCommand || !selectedCommand}
                style={{ padding: '10px 15px', background: '#2ea043', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold' }}
              >
                {loadingCommand ? "..." : "Ejecutar"}
              </button>
            </div>
          </div>

          <div>
            <label style={{ display: 'block', color: '#c9d1d9', fontSize: '13px', marginBottom: '5px' }}>Comando personalizado</label>
            <div style={{ display: 'flex', gap: '10px' }}>
              <input
                value={customCommand}
                onChange={(event) => setCustomCommand(event.target.value)}
                placeholder="Ej: nmap -sC recon-lab"
                style={{ flex: 1, padding: '10px', background: '#0d1117', color: '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px', fontFamily: 'monospace' }}
              />
              <button
                type="button"
                onClick={() => handleTerminalCommand(customCommand)}
                disabled={loadingCommand || !customCommand.trim()}
                style={{ padding: '10px 15px', background: '#21262d', color: '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px', cursor: 'pointer' }}
              >
                Lanzar
              </button>
            </div>
          </div>
        </article>
      </div>

      {/* CONSOLA DE SALIDA LIMPIA (TIPO LINUX) */}
      <article className="practice-console" style={{ marginTop: '10px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#21262d', padding: '10px 15px', borderTopLeftRadius: '8px', borderTopRightRadius: '8px', border: '1px solid #30363d', borderBottom: 'none' }}>
          <div style={{ display: 'flex', gap: '8px' }}>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }}></span>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }}></span>
            <span style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }}></span>
          </div>
          <strong style={{ color: '#8b949e', fontSize: '12px', fontFamily: 'monospace' }}>cyberlab@atacante:~</strong>
          <button 
            onClick={clearConsole}
            style={{ background: 'transparent', border: 'none', color: '#58a6ff', fontSize: '12px', cursor: 'pointer' }}
          >
            Limpiar (clear)
          </button>
        </div>

        <pre style={{ 
          margin: 0, 
          background: '#0d1117', 
          color: '#3fb950', 
          padding: '20px', 
          minHeight: '250px', 
          maxHeight: '400px', 
          overflowY: 'auto', 
          fontFamily: "'Courier New', Courier, monospace", 
          fontSize: '14px', 
          lineHeight: '1.5',
          borderBottomLeftRadius: '8px', 
          borderBottomRightRadius: '8px', 
          border: '1px solid #30363d' 
        }}>
          {outputHistory.map((line, idx) => (
            <div key={idx} style={{ whiteSpace: 'pre-wrap', color: line.startsWith('[ERROR]') ? '#ff7b72' : line.includes('SEGURIDAD:') ? '#d2a8ff' : '#3fb950' }}>
              {line}
            </div>
          ))}
          <div ref={consoleBottomRef} />
        </pre>
      </article>

    </section>
  );
}