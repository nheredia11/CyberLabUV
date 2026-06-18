import { useMemo, useState } from "react";
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
    "curl http://recon-lab:5000/health",
    "curl http://127.0.0.1:8083/events",
  ],
  S02: [
    "curl -i http://127.0.0.1:8081/health",
    "curl http://127.0.0.1:8081/attempts",
    "hydra -l estudiante -P wordlists/demo.txt localhost http-post-form",
  ],
  S03: [
    "curl 'http://127.0.0.1:8084/web/search?q=test'",
    "curl 'http://127.0.0.1:8084/web/file?name=readme.txt'",
    "curl 'http://127.0.0.1:8084/events'",
  ],
  S04: [
    "curl -i http://127.0.0.1:8085/health",
    "curl http://127.0.0.1:8085/events",
  ],
  S05: [
    "curl -i http://127.0.0.1:8086/health",
    "curl http://127.0.0.1:8086/events",
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
  const [output, setOutput] = useState(
    "Selecciona una acción del escenario o ejecuta un comando guiado."
  );

  const commands = useMemo(() => {
    return SAFE_COMMANDS[scenarioId] || [];
  }, [scenarioId]);

  async function handleScenarioAction(action) {
    try {
      setLoadingAction(action);
      setOutput(`Ejecutando acción "${action}" para ${scenarioId}...`);

      const response = await runScenarioAction({
        user_id: userId,
        scenario_id: scenarioId,
        action,
      });

      setOutput(JSON.stringify(response, null, 2));

      if (onScenarioEvent) {
        onScenarioEvent(response);
      }
    } catch (error) {
      setOutput(`Error ejecutando la acción: ${error.message}`);
    } finally {
      setLoadingAction("");
    }
  }

  async function handleTerminalCommand(commandValue) {
    const command = commandValue?.trim();

    if (!command) {
      setOutput("Escribe o selecciona un comando antes de ejecutarlo.");
      return;
    }

    try {
      setLoadingCommand(true);
      setOutput(`Ejecutando comando guiado:\n${command}`);

      const response = await runTerminalCommand({
        user_id: userId,
        scenario_id: scenarioId,
        command,
      });

      setOutput(JSON.stringify(response, null, 2));
    } catch (error) {
      setOutput(`Error ejecutando el comando: ${error.message}`);
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
    <section className="practice-shell">
      <div className="practice-hero">
        <span className="eyebrow">Práctica local controlada</span>
        <h2>{scenarioId} · Laboratorio CyberLab</h2>
        <p>
          Desde esta sección puedes iniciar el escenario Docker, abrir el
          laboratorio local, consultar el estado y ejecutar comandos guiados con
          el usuario real de la sesión.
        </p>

        <div className="practice-meta-grid">
          <article>
            <span>Estudiante</span>
            <strong>{userId}</strong>
          </article>

          <article>
            <span>Escenario</span>
            <strong>{scenarioId}</strong>
          </article>

          <article>
            <span>Laboratorio</span>
            <strong>{labUrl || "No aplica"}</strong>
          </article>
        </div>
      </div>

      <div className="practice-grid">
        <article className="practice-card">
          <h3>Control del escenario</h3>
          <p>
            Estas acciones llaman al backend, y el backend se encarga de ejecutar
            Docker Compose de forma controlada.
          </p>

          <div className="practice-actions">
            {["start", "status", "reset", "stop"].map((action) => (
              <button
                key={action}
                type="button"
                className={action === "stop" ? "danger-button" : ""}
                onClick={() => handleScenarioAction(action)}
                disabled={Boolean(loadingAction)}
              >
                {loadingAction === action
                  ? "Ejecutando..."
                  : getActionLabel(action)}
              </button>
            ))}
          </div>

          {labUrl && (
            <a
              className="open-lab-button"
              href={labUrl}
              target="_blank"
              rel="noreferrer"
            >
              Abrir laboratorio local
            </a>
          )}
        </article>

        <article className="practice-card">
          <h3>Terminal guiada</h3>
          <p>
            Usa comandos permitidos por el backend para mantener la práctica en
            un entorno académico, ético y seguro.
          </p>

          <label>
            Comando sugerido
            <select
              value={selectedCommand}
              onChange={(event) => setSelectedCommand(event.target.value)}
            >
              {commands.length === 0 && (
                <option value="">No hay comandos definidos</option>
              )}

              {commands.map((command) => (
                <option key={command} value={command}>
                  {command}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            onClick={() => handleTerminalCommand(selectedCommand)}
            disabled={loadingCommand || !selectedCommand}
          >
            {loadingCommand ? "Ejecutando..." : "Ejecutar comando sugerido"}
          </button>

          <label>
            Comando personalizado permitido
            <input
              value={customCommand}
              onChange={(event) => setCustomCommand(event.target.value)}
              placeholder="Escribe un comando permitido por el backend"
            />
          </label>

          <button
            type="button"
            className="secondary-button"
            onClick={() => handleTerminalCommand(customCommand)}
            disabled={loadingCommand || !customCommand.trim()}
          >
            Ejecutar comando personalizado
          </button>
        </article>
      </div>

      <article className="practice-console">
        <div className="console-head">
          <span></span>
          <span></span>
          <span></span>
          <strong>Salida del backend</strong>
        </div>

        <pre>{output}</pre>
      </article>
    </section>
  );
}