import { 
  BookOpen, 
  ShieldCheck, 
  FileText, 
  CheckCircle2, 
  Server, 
  Cpu, 
  Lock, 
  TerminalSquare, 
  ExternalLink 
} from 'lucide-react';

// Estilos compartidos para mantener coherencia con el Dark Theme
const pageStyle = { maxWidth: '1000px', margin: '0 auto', padding: '20px', color: '#c9d1d9', fontFamily: 'system-ui, -apple-system, sans-serif' };
const headerStyle = { display: 'flex', alignItems: 'center', gap: '10px', fontSize: '24px', color: '#c9d1d9', margin: '0 0 10px 0', paddingBottom: '15px', borderBottom: '1px solid #30363d' };
const cardStyle = { background: '#161b22', padding: '25px', borderRadius: '8px', border: '1px solid #30363d', marginBottom: '20px' };
const gridStyle = { display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '20px', marginTop: '20px' };

export function Resources() {
  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <h2 style={headerStyle}><BookOpen color="#58a6ff" /> Biblioteca de Recursos</h2>
        <p style={{ color: '#8b949e', lineHeight: '1.6' }}>
          Documentación oficial y marcos de referencia internacionales utilizados para el diseño de los escenarios de CyberLabUV.
        </p>

        <div style={gridStyle}>
          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0', display: 'flex', justifyContent: 'space-between' }}>
              OWASP Top 10 <ExternalLink size={16} color="#8b949e" />
            </h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: '0 0 15px 0' }}>Estándar de concientización para desarrolladores sobre la seguridad de las aplicaciones web. Base del Módulo S03.</p>
            <span style={{ fontSize: '12px', background: '#21262d', padding: '4px 8px', borderRadius: '4px' }}>Inyección SQL, XSS, Broken Auth</span>
          </article>

          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0', display: 'flex', justifyContent: 'space-between' }}>
              MITRE ATT&CK® <ExternalLink size={16} color="#8b949e" />
            </h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: '0 0 15px 0' }}>Base de conocimiento global de tácticas y técnicas de adversarios basada en observaciones del mundo real.</p>
            <span style={{ fontSize: '12px', background: '#21262d', padding: '4px 8px', borderRadius: '4px' }}>Reconocimiento, Acceso Inicial</span>
          </article>

          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0', display: 'flex', justifyContent: 'space-between' }}>
              NIST Cybersecurity Framework <ExternalLink size={16} color="#8b949e" />
            </h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: '0 0 15px 0' }}>Directrices para mitigar riesgos de ciberseguridad organizacional. Aplicado en la fase teórica de los laboratorios.</p>
            <span style={{ fontSize: '12px', background: '#21262d', padding: '4px 8px', borderRadius: '4px' }}>Identificar, Proteger, Detectar</span>
          </article>
        </div>
      </div>
    </div>
  );
}

export function Templates() {
  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <h2 style={headerStyle}><FileText color="#d2a8ff" /> Directrices de Evidencia</h2>
        <p style={{ color: '#8b949e', lineHeight: '1.6' }}>
          Para cumplir con el modelo de evaluación cualitativa propuesto en este simulador, los estudiantes deben reportar sus hallazgos siguiendo estándares profesionales.
        </p>

        <div style={{ marginTop: '30px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
          <div style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d', borderLeft: '4px solid #d2a8ff' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#c9d1d9' }}>1. Banderas (Flags)</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              Una flag es una cadena de texto única que prueba que lograste explotar una vulnerabilidad (Ej. la versión oculta de un servicio o una contraseña desencriptada). Cópiala exactamente como sale en tu consola.
            </p>
          </div>

          <div style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d', borderLeft: '4px solid #58a6ff' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#c9d1d9' }}>2. Ejecución Controlada</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              No uses herramientas de escaneo masivo (como Nessus) a menos que se indique explícitamente. Prioriza el uso de <code>nmap</code>, <code>curl</code> y <code>hydra</code> respetando la lista blanca del servidor.
            </p>
          </div>

          <div style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d', borderLeft: '4px solid #3fb950' }}>
            <h3 style={{ margin: '0 0 10px 0', color: '#c9d1d9' }}>3. Ética Hacker</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              Todo el conocimiento adquirido en esta plataforma es estrictamente académico. El ataque a sistemas ajenos sin autorización es un delito. 
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export function Quality() {
  return (
    <div style={pageStyle}>
      <div style={cardStyle}>
        <h2 style={headerStyle}><ShieldCheck color="#3fb950" /> Arquitectura y Calidad Técnica</h2>
        <p style={{ color: '#8b949e', lineHeight: '1.6' }}>
          CyberLabUV ha sido diseñado priorizando la escalabilidad y la seguridad del host local del estudiante. 
          A continuación, se detalla la infraestructura tecnológica que soporta la plataforma.
        </p>

        <div style={gridStyle}>
          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <Cpu size={28} color="#58a6ff" style={{ marginBottom: '15px' }} />
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0' }}>Arquitectura Híbrida</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              Implementación de simulaciones ligeras en navegador (WebAssembly) combinadas con laboratorios reales contenerizados mediante Docker, reduciendo el consumo de RAM.
            </p>
          </article>

          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <Lock size={28} color="#d2a8ff" style={{ marginBottom: '15px' }} />
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0' }}>Hardening & Lista Blanca</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              El backend actúa como un firewall de comandos. Implementa validación estricta (Allow-list) que bloquea inyecciones como <code>rm -rf</code> o escaladas de privilegios.
            </p>
          </article>

          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <Server size={28} color="#e3b341" style={{ marginBottom: '15px' }} />
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0' }}>Límites de Recursos</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              Cada escenario vulnerable está restringido nativamente en su <code>docker-compose.yml</code> a un máximo de <strong>256MB de RAM</strong> y <strong>0.5 cpus</strong>, garantizando que equipos de gama baja no se congelen.
            </p>
          </article>

          <article style={{ background: '#0d1117', padding: '20px', borderRadius: '6px', border: '1px solid #30363d' }}>
            <TerminalSquare size={28} color="#3fb950" style={{ marginBottom: '15px' }} />
            <h3 style={{ color: '#c9d1d9', margin: '0 0 10px 0' }}>Validación Pedagógica</h3>
            <p style={{ color: '#8b949e', fontSize: '14px', margin: 0 }}>
              Evaluación cualitativa sin notas numéricas. El docente visualiza las evidencias mediante un Dashboard analítico y provee feedback directo al estudiante.
            </p>
          </article>
        </div>
      </div>
    </div>
  );
}