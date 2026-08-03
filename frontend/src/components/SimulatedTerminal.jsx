import { useState, useRef, useEffect } from "react";

export default function SimulatedTerminal({ scenarioId }) {
  const [history, setHistory] = useState([
    "Bienvenido a la terminal simulada de CyberLab.",
    "Escribe 'help' para ver los comandos disponibles.",
  ]);
  const [input, setInput] = useState("");
  const bottomRef = useRef(null);

  // Mocks de respuestas estáticas (¡Esto no consume recursos Docker!)
  const MOCK_RESPONSES = {
    "S01": {
      "nmap -sV recon-lab": `
Starting Nmap 7.93 ( https://nmap.org )
Nmap scan report for recon-lab (192.168.1.10)
Host is up (0.00012s latency).
Not shown: 999 closed tcp ports (reset)
PORT     STATE SERVICE VERSION
5000/tcp open  http    Werkzeug httpd 2.2.2 (Python 3.10.8)
Nmap done: 1 IP address (1 host up) scanned in 6.42 seconds`,
      "help": "Comandos permitidos en este escenario: nmap -sV recon-lab, clear",
    }
  };

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [history]);

  const handleCommand = (e) => {
    if (e.key === "Enter") {
      const command = input.trim();
      const newHistory = [...history, `cyberlab@student:~$ ${command}`];
      
      if (command === "clear") {
        setHistory([]);
      } else if (command) {
        // Buscar si existe una respuesta mockeada para este escenario y comando
        const scenarioMocks = MOCK_RESPONSES[scenarioId] || MOCK_RESPONSES["S01"];
        const response = scenarioMocks[command] || "Comando no reconocido o no soportado en esta simulación. Prueba con 'help'.";
        newHistory.push(response);
        setHistory(newHistory);
      }
      
      setInput("");
    }
  };

  return (
    <div style={{ backgroundColor: "#1e1e1e", color: "#00ff00", padding: "20px", borderRadius: "8px", fontFamily: "monospace", minHeight: "300px", display: "flex", flexDirection: "column" }}>
      <div style={{ flex: 1, overflowY: "auto", whiteSpace: "pre-wrap" }}>
        {history.map((line, idx) => (
          <div key={idx}>{line}</div>
        ))}
        <div ref={bottomRef} />
      </div>
      <div style={{ display: "flex", marginTop: "10px" }}>
        <span style={{ marginRight: "10px" }}>cyberlab@student:~$</span>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleCommand}
          style={{ flex: 1, backgroundColor: "transparent", border: "none", color: "#00ff00", outline: "none", fontFamily: "monospace", fontSize: "16px" }}
          autoFocus
        />
      </div>
    </div>
  );
}