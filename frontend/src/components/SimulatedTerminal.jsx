import { useState, useRef, useEffect } from "react";
import { api } from "../lib/api";

export default function SimulatedTerminal({ scenarioId }) {
  const [history, setHistory] = useState([
    "Bienvenido a la terminal interactiva de CyberLab.",
    "Escribe un comando válido (ej. nmap, curl, help) o usa 'clear' para limpiar.",
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  // Mocks de respaldo por si el backend está en modo seco (dry-run) o sin contenedor activo
  const MOCK_RESPONSES = {
    "S01": {
      "nmap -sV 10.10.10.20": `[SIMULADO] Starting Nmap 7.93...\nPORT   STATE SERVICE VERSION\n22/tcp open  ssh     OpenSSH 8.9\n80/tcp open  http    nginx 1.22`,
      "help": "Comandos simulados disponibles: nmap -sV 10.10.10.20, curl http://localhost:8081, clear",
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleCommand = async (e) => {
    if (e.key === "Enter" && !loading) {
      const command = input.trim();
      if (!command) return;

      if (command === "clear") {
        setHistory([]);
        setInput("");
        return;
      }

      const newHistory = [...history, `cyberlab@student:~$ ${command}`];
      setHistory(newHistory);
      setInput("");
      setLoading(true);

      try {
        // Llamada real al backend protegido con token y sesión Docker
        const res = await api.post(`/api/scenarios/${scenarioId}/command`, {
          scenario_id: scenarioId,
          command: command
        });
        
        setHistory((prev) => [...prev, res.output || "Comando ejecutado con éxito."]);
      } catch (err) {
        console.warn("Fallo el comando en backend real, usando respaldo local:", err);
        // Fallback a mocks locales si el contenedor no está activo
        const scenarioMocks = MOCK_RESPONSES[scenarioId] || MOCK_RESPONSES["S01"];
        const response = scenarioMocks[command] || (err.response?.data?.detail || "Comando no permitido o contenedor inactivo. Inicia el escenario primero.");
        setHistory((prev) => [...prev, response]);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div style={{ backgroundColor: "#1e1e1e", color: "#00ff00", padding: "20px", borderRadius: "8px", fontFamily: "monospace", minHeight: "300px", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, overflowY: "auto", whiteSpace: "pre-wrap" }}>
        {history.map((line, idx) => (
          <div key={idx}>{line}</div>
        ))}
        {loading && <div style={{ color: "#ffff00" }}>Ejecutando en entorno aislado...</div>}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: "flex", marginTop: "10px" }}>
        <span style={{ marginRight: "10px" }}>cyberlab@student:~$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleCommand}
          disabled={loading}
          style={{ flex: 1, backgroundColor: "transparent", border: "none", color: "#00ff00", outline: "none", fontFamily: "monospace", fontSize: "16px" }}
          autoFocus
        />
      </div>
    </div>
  );
}