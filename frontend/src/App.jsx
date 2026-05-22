import { useEffect, useMemo, useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Topbar from './components/Topbar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import LearningRoute from './pages/LearningRoute.jsx';
import Practice from './pages/Practice.jsx';
import Results from './pages/Results.jsx';
import TeacherAnalytics from './pages/TeacherAnalytics.jsx';
import { Quality, Resources, Templates } from './pages/StaticPages.jsx';
import { api } from './lib/api.js';
import './styles/theme.css';

export default function App() {
  const [view, setView] = useState('dashboard');
  const [theme, setTheme] = useState('light');
  const [dashboard, setDashboard] = useState(null);
  const [selectedModule, setSelectedModule] = useState('S02');
  const refreshDashboard = () => api.dashboard('ana').then(setDashboard).catch(console.error);
  useEffect(() => { document.documentElement.dataset.theme = theme; }, [theme]);
  useEffect(() => { refreshDashboard(); }, []);
  const titles = useMemo(() => ({
    dashboard: ['Bienvenida, Ana 👋', 'Continúa tu ruta de aprendizaje y fortalece tus habilidades de ciberseguridad.'],
    route: ['Ruta de aprendizaje', 'Teoría, práctica, checkpoints y evaluación formativa.'],
    practice: ['Simulación local', 'Control de escenarios Docker y registro de evidencias.'],
    results: ['Resultados de la práctica', 'Retroalimentación, desempeño y próximos pasos.'],
    teacher: ['Panel docente', 'Seguimiento, criterios de evaluación y analíticas.'],
    resources: ['Biblioteca de recursos', 'Material de apoyo para el laboratorio.'],
    templates: ['Plantillas', 'Formatos para evidencias y pruebas.'],
    quality: ['Cadena de calidad', 'Validación técnica, funcional y pedagógica.'],
  }), []);
  const [title, subtitle] = titles[view] || titles.dashboard;
  return <div className="app-shell"><Sidebar view={view} setView={setView} theme={theme} setTheme={setTheme}/><main className="main"><Topbar title={title} subtitle={subtitle}/>{view === 'dashboard' && <Dashboard data={dashboard} setView={setView} setSelectedModule={setSelectedModule}/>} {view === 'route' && <LearningRoute selectedModule={selectedModule} setSelectedModule={setSelectedModule} refreshDashboard={refreshDashboard}/>} {view === 'practice' && <Practice/>} {view === 'results' && <Results data={dashboard}/>} {view === 'teacher' && <TeacherAnalytics/>} {view === 'resources' && <Resources/>} {view === 'templates' && <Templates/>} {view === 'quality' && <Quality/>}</main></div>;
}
