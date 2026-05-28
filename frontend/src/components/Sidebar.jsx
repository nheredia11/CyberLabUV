import { Activity, BarChart3, BookOpen, Boxes, ClipboardCheck, Home, Library, Moon, PlayCircle, Shield, Sun } from 'lucide-react';

const items = [
  { id: 'dashboard', label: 'Dashboard', icon: Home },
  { id: 'route', label: 'Ruta de aprendizaje', icon: BookOpen },
  { id: 'practice', label: 'Práctica local', icon: PlayCircle },
  { id: 'results', label: 'Resultados', icon: ClipboardCheck },
  { id: 'teacher', label: 'Analíticas docente', icon: BarChart3 },
];
const tools = [
  { id: 'resources', label: 'Biblioteca de recursos', icon: Library },
  { id: 'templates', label: 'Plantillas', icon: Boxes },
  { id: 'quality', label: 'Cadena de calidad', icon: Activity },
];

export default function Sidebar({ view, setView, theme, setTheme }) {
  const render = (item) => {
    const Icon = item.icon;
    return <button key={item.id} className={`nav-item ${view === item.id ? 'active' : ''}`} onClick={() => setView(item.id)}><Icon size={18}/>{item.label}</button>;
  };
  return <aside className="sidebar">
    <div className="brand"><div className="logo"><Shield size={24}/></div><div><div>CyberLab</div><small>Simulador de ciberseguridad</small></div></div>
    <div className="nav-group"><div className="nav-title">Navegación</div>{items.map(render)}</div>
    <div className="nav-group"><div className="nav-title">Herramientas</div>{tools.map(render)}</div>
    <button className="nav-item" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>{theme === 'dark' ? <Sun size={18}/> : <Moon size={18}/>}Modo {theme === 'dark' ? 'claro' : 'oscuro'}</button>
    <div className="sync-card"><strong>Sincronización local</strong><p>App local activa<br/>Sync automática cada 30 seg.</p><button className="btn secondary" onClick={() => setView('practice')}>Ver estado</button></div>
  </aside>;
}
