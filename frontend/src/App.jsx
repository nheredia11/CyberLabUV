import { useEffect, useMemo, useState } from 'react';
import Sidebar from './components/Sidebar.jsx';
import Topbar from './components/Topbar.jsx';
import Dashboard from './pages/Dashboard.jsx';
import LearningRoute from './pages/LearningRoute.jsx';
import Practice from './pages/Practice.jsx';
import Results from './pages/Results.jsx';
import TeacherAnalytics from './pages/TeacherAnalytics.jsx';
import Login from './pages/Login.jsx';
import { Quality, Resources, Templates } from './pages/StaticPages.jsx';
import { api } from './lib/api.js';
import './styles/theme.css';

export default function App() {
  const [view, setView] = useState('dashboard');
  const [theme, setTheme] = useState('light');
  const [dashboard, setDashboard] = useState(null);
  const [selectedModule, setSelectedModule] = useState('S02');
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cyberlab_user');
    return saved ? JSON.parse(saved) : null;
  });

  const userId = user?.id || 'ana';

  const refreshDashboard = () =>
    api.dashboard(userId).then(setDashboard).catch(console.error);

  function handleLogout() {
    localStorage.removeItem('cyberlab_user');
    localStorage.removeItem('cyberlab_token');
    setUser(null);
    setDashboard(null);
    setView('dashboard');
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (user) {
      refreshDashboard();
    }
  }, [userId]);

  const titles = useMemo(() => ({
    dashboard: [
      'Panel de aprendizaje',
      'Progreso, laboratorio y retroalimentación del estudiante.',
    ],
    route: [
      'Ruta de aprendizaje',
      'Teoría, práctica, checkpoints y evaluación formativa.',
    ],
    practice: [
      'Laboratorio local',
      'Escenario Docker, terminal guiada y evidencias.',
    ],
    results: [
      'Resultados',
      'Desempeño, fortalezas y próximos pasos.',
    ],
    teacher: [
      'Panel docente',
      'Seguimiento, criterios de evaluación y analíticas.',
    ],
    resources: [
      'Biblioteca de recursos',
      'Material de apoyo para el laboratorio.',
    ],
    templates: [
      'Plantillas',
      'Formatos para evidencias y pruebas.',
    ],
    quality: [
      'Cadena de calidad',
      'Validación técnica, funcional y pedagógica.',
    ],
  }), [user]);

  if (!user) {
    return <Login 
      onLogin={setUser}
      theme={theme}
      setTheme={setTheme} 
    />;
  }

  const [title, subtitle] = titles[view] || titles.dashboard;

  return (
    <div className="app-shell">
      <Sidebar
        view={view}
        setView={setView}
        theme={theme}
        setTheme={setTheme}
      />

      <main className="main">
        <Topbar
          title={title}
          subtitle={subtitle}
          user={user}
          onLogout={handleLogout}
        />

        {view === 'dashboard' && (
          <Dashboard
            data={dashboard}
            user={user}
            userId={userId}
            setView={setView}
            setSelectedModule={setSelectedModule}
            refreshDashboard={refreshDashboard}
          />
        )}

        {view === 'route' && (
          <LearningRoute
            selectedModule={selectedModule}
            setSelectedModule={setSelectedModule}
            refreshDashboard={refreshDashboard}
            userId={userId}
            setView={setView}
          />
        )}

        {view === 'practice' && <Practice userId={userId} />}

        {view === 'results' && (
          <Results
            data={dashboard}
            user={user}
            setView={setView}
          />
        )}
        
        {view === 'teacher' && <TeacherAnalytics />}

        {view === 'resources' && <Resources />}

        {view === 'templates' && <Templates />}

        {view === 'quality' && <Quality />}
      </main>
    </div>
  );
}