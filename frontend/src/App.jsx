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
  const [theme, setTheme] = useState('dark');
  const [dashboard, setDashboard] = useState(null);
  const [selectedModule, setSelectedModule] = useState('S02');
  
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('cyberlab_user');
    if (!saved || saved === 'undefined' || saved === 'null') {
      return null;
    }
    try {
      const parsed = JSON.parse(saved);
      if (parsed) {
        parsed.id = parsed.id || parsed.user_id;
        parsed.user_id = parsed.user_id || parsed.id;
      }
      return parsed;
    } catch (e) {
      console.error("Error al parsear cyberlab_user desde localStorage:", e);
      return null;
    }
  });

  const [view, setView] = useState(() => {
    if (user?.role === 'teacher') return 'teacher';
    return 'dashboard';
  });

  // ID seguro del usuario o null si no hay sesión
  const userId = user?.id || user?.user_id || null;

  const refreshDashboard = () => {
    if (!userId) return;
    api.dashboard(userId).then(setDashboard).catch((err) => {
      console.error("Error cargando dashboard:", err);
      if (err.status === 401) {
        // Si hay un 401 real, limpiamos la sesión expirada de forma limpia
        handleLogout();
      }
    });
  };

  function handleLogout() {
    localStorage.removeItem('cyberlab_user');
    localStorage.removeItem('cyberlab_token');
    localStorage.removeItem('cyberlab_session_token');
    localStorage.removeItem('auth_token');
    setUser(null);
    setDashboard(null);
    setView('dashboard');
  }

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    if (user && userId) {
      setView(user.role === 'teacher' ? 'teacher' : 'dashboard');
      refreshDashboard();
    }
  }, [userId, user?.role]);

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
  }), []);

  if (!user || !userId) {
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
        userRole={user.role}
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

        {view === 'route' && user.role !== 'teacher' && (
          <LearningRoute
            selectedModule={selectedModule}
            setSelectedModule={setSelectedModule}
            refreshDashboard={refreshDashboard}
            userId={userId}
            setView={setView}
          />
        )}

        {view === 'practice' && user.role !== 'teacher' && <Practice userId={userId} />}

        {view === 'results' && user.role !== 'teacher' && (
          <Results
            data={dashboard}
            user={user}
            setView={setView}
          />
        )}
        
        {view === 'teacher' && user.role === 'teacher' && <TeacherAnalytics />}

        {view === 'resources' && <Resources />}
        {view === 'templates' && <Templates />}
        {view === 'quality' && <Quality />}
      </main>
    </div>
  );
}