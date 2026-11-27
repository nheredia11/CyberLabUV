import { useMemo } from "react";
import {
  Award,
  BookOpen,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  Clock3,
  Flame,
  GraduationCap,
  Lightbulb,
  PlayCircle,
  RefreshCw,
  ShieldCheck,
  Target,
  TerminalSquare,
  Trophy,
  UserRound,
} from "lucide-react";

// NUEVO: ProgressBar nativa
function ProgressBar({ value }) {
  const percent = Math.max(0, Math.min(100, Number(value) || 0));
  return (
    <div style={{ width: '100%', backgroundColor: 'var(--surface-raised)', borderRadius: '4px', height: '8px', overflow: 'hidden', margin: '8px 0' }}>
      <div 
        style={{ 
          height: '100%', 
          backgroundColor: percent >= 85 ? 'var(--ok)' : percent >= 50 ? 'var(--violet)' : 'var(--link)', 
          width: `${percent}%`,
          transition: 'width 0.4s ease-in-out'
        }} 
      />
    </div>
  );
}

function clamp(value = 0) {
  return Math.max(0, Math.min(100, Number(value) || 0));
}

function firstName(name = "") {
  return name?.split(" ")?.[0] || "estudiante";
}

function getRecommendedModule(modules = []) {
  return (
    modules.find((module) => module.progress?.percent > 0 && module.progress?.percent < 100) ||
    modules.find((module) => module.progress?.percent === 0) ||
    modules[0]
  );
}

export default function Dashboard({ data, user, userId, setView, setSelectedModule, refreshDashboard }) {
  const studentName = firstName(user?.name);

  const modules = data?.modules || [];
  const recommended = useMemo(() => getRecommendedModule(modules), [modules]);

  const generalPercent = clamp(data?.general_percent);
  const completedModules = data?.completed_modules || 0;
  const totalModules = data?.total_modules || modules.length || 0;
  
  const activeModulesCount = modules.filter((m) => clamp(m.progress?.percent) > 0).length;

  const currentPercent = clamp(recommended?.progress?.percent);

  function handleStartModule(moduleId) {
    if (setSelectedModule) setSelectedModule(moduleId);
    if (setView) setView("route");
  }

  function openRecommended() {
    handleStartModule(recommended?.id || "S02");
  }

  if (!data) {
    return (
      <div style={{ padding: '60px', textAlign: 'center', color: 'var(--ink-muted)' }}>
        <h3>Cargando panel de aprendizaje...</h3>
        <p>Sincronizando con el servidor local de CyberLab.</p>
      </div>
    );
  }

  return (
    <div className="dashboard-page" style={{ maxWidth: '1200px', margin: '0 auto', padding: '20px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
      
      {/* SECCIÓN 1: BIENVENIDA Y RESUMEN GENERAL */}
      <section style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '30px', background: 'var(--surface)', padding: '30px', borderRadius: '8px', border: '1px solid var(--line)' }}>
        <div>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: '5px', fontSize: '12px', background: 'var(--surface-raised)', color: 'var(--ink)', padding: '4px 10px', borderRadius: '12px', marginBottom: '10px' }}>
            <ShieldCheck size={15} /> Sesión activa
          </span>
          <h1 style={{ color: 'var(--ink)', margin: '10px 0', fontSize: '28px' }}>
            Hola, {studentName} 👋
          </h1>
          <p style={{ color: 'var(--ink-muted)', margin: 0, fontSize: '15px' }}>
            {generalPercent === 0
              ? "Bienvenido al simulador. Empieza tu entrenamiento con el módulo de inducción."
              : generalPercent >= 100
              ? "¡Felicidades! Has completado todos los laboratorios disponibles."
              : `Llevas un ${generalPercent}% de avance en tu formación. ¡Sigue así!`}
          </p>
          
          <div style={{ display: 'flex', gap: '10px', marginTop: '20px' }}>
            <button onClick={openRecommended} style={{ padding: '10px 20px', background: 'var(--btn-ok)', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <Target size={17} /> Continuar misión
            </button>
            <button onClick={() => setView('practice')} style={{ padding: '10px 20px', background: 'var(--surface-raised)', color: 'var(--ink)', border: '1px solid var(--line)', borderRadius: '6px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}>
              <TerminalSquare size={17} /> Laboratorio Libre
            </button>
            <button onClick={refreshDashboard} style={{ padding: '10px', background: 'transparent', color: 'var(--ink-muted)', border: 'none', cursor: 'pointer' }} title="Actualizar datos">
              <RefreshCw size={17} />
            </button>
          </div>
        </div>
        
        <div style={{ textAlign: 'center', background: 'var(--surface-sunken)', padding: '20px 30px', borderRadius: '8px', border: '1px solid var(--line)', minWidth: '150px' }}>
          <strong style={{ display: 'block', fontSize: '36px', color: 'var(--ok)', lineHeight: '1' }}>{generalPercent}%</strong>
          <span style={{ color: 'var(--ink-muted)', fontSize: '13px', display: 'block', marginTop: '5px' }}>Progreso Global</span>
          <ProgressBar value={generalPercent} />
        </div>
      </section>

      {/* SECCIÓN 2: TARJETAS DE ESTADÍSTICAS */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '20px', marginBottom: '40px' }}>
        <div style={{ background: 'var(--surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'var(--surface-raised)', padding: '12px', borderRadius: '8px', color: 'var(--link)' }}><BookOpen size={24} /></div>
          <div>
            <strong style={{ fontSize: '22px', color: 'var(--ink)', display: 'block' }}>{completedModules} / {totalModules}</strong>
            <span style={{ color: 'var(--ink-muted)', fontSize: '13px' }}>Módulos completados</span>
          </div>
        </div>
        <div style={{ background: 'var(--surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'var(--surface-raised)', padding: '12px', borderRadius: '8px', color: 'var(--violet)' }}><TerminalSquare size={24} /></div>
          <div>
            <strong style={{ fontSize: '22px', color: 'var(--ink)', display: 'block' }}>{activeModulesCount}</strong>
            <span style={{ color: 'var(--ink-muted)', fontSize: '13px' }}>Laboratorios en curso</span>
          </div>
        </div>
        <div style={{ background: 'var(--surface)', padding: '20px', borderRadius: '8px', border: '1px solid var(--line)', display: 'flex', alignItems: 'center', gap: '15px' }}>
          <div style={{ background: 'var(--surface-raised)', padding: '12px', borderRadius: '8px', color: 'var(--warn)' }}><Award size={24} /></div>
          <div>
            <strong style={{ fontSize: '22px', color: 'var(--ink)', display: 'block' }}>{data?.points || 0}</strong>
            <span style={{ color: 'var(--ink-muted)', fontSize: '13px' }}>Puntos de experiencia</span>
          </div>
        </div>
      </section>

      {/* SECCIÓN 3: LISTADO DINÁMICO DE MÓDULOS */}
      <section>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid var(--line)', paddingBottom: '10px', marginBottom: '20px' }}>
          <h2 style={{ color: 'var(--ink)', margin: 0, fontSize: '20px', display: 'flex', alignItems: 'center', gap: '10px' }}>
            <GraduationCap size={22} color="var(--ink-muted)" />
            Ruta de Aprendizaje
          </h2>
          <button onClick={() => setView('route')} style={{ background: 'transparent', color: 'var(--link)', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', fontSize: '14px' }}>
            Ver detalles <ChevronRight size={16} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}>
          {modules.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', background: 'var(--surface)', borderRadius: '8px', border: '1px dashed var(--line)', color: 'var(--ink-muted)' }}>
              No se encontraron módulos. Verifica la conexión con el servidor.
            </div>
          ) : (
            modules.map((mod) => {
              const pct = clamp(mod.progress?.percent);
              const isCompleted = pct === 100;
              const isStarted = pct > 0 && pct < 100;

              return (
                <article 
                  key={mod.id} 
                  style={{ background: 'var(--surface)', padding: '20px 25px', borderRadius: '8px', border: `1px solid ${mod.id === recommended?.id ? 'var(--link)' : 'var(--line)'}`, display: 'flex', alignItems: 'center', justifyContent: 'space-between', cursor: 'pointer' }} 
                  onClick={() => handleStartModule(mod.id)}
                >
                  <div style={{ flex: 1, paddingRight: '20px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                      <span style={{ background: isCompleted ? 'var(--btn-ok)20' : isStarted ? 'var(--violet)20' : 'var(--surface-raised)', color: isCompleted ? 'var(--ok)' : isStarted ? 'var(--violet)' : 'var(--ink-muted)', padding: '4px 10px', borderRadius: '4px', fontSize: '12px', fontWeight: 'bold' }}>
                        {mod.id}
                      </span>
                      <h3 style={{ margin: 0, color: 'var(--ink)', fontSize: '18px' }}>{mod.titulo || mod.title}</h3>
                      {isCompleted && <CheckCircle2 size={18} color="var(--ok)" />}
                    </div>
                    <p style={{ margin: 0, color: 'var(--ink-muted)', fontSize: '14px', lineHeight: '1.5' }}>
                      {mod.descripcion || mod.description || "Escenario práctico de ciberseguridad."}
                    </p>
                  </div>

                  <div style={{ width: '220px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', borderLeft: '1px solid var(--line)', paddingLeft: '20px' }}>
                    <span style={{ fontSize: '13px', color: 'var(--ink-muted)', marginBottom: '5px' }}>{pct}% completado</span>
                    <ProgressBar value={pct} />
                    <span style={{ color: isCompleted ? 'var(--ok)' : 'var(--link)', fontSize: '13px', fontWeight: 'bold', marginTop: '10px' }}>
                      {isCompleted ? "Repasar" : isStarted ? "Continuar" : "Iniciar"} 
                    </span>
                  </div>
                </article>
              );
            })
          )}
        </div>
      </section>
      
    </div>
  );
}