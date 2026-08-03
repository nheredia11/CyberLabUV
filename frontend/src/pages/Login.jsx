import { useEffect, useRef, useState } from 'react';
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  GraduationCap,
  LockKeyhole,
  Moon,
  ShieldCheck,
  Sun,
  TerminalSquare,
  User,
  Users
} from 'lucide-react';
import { api } from '../lib/api.js';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

function loadGoogleScript() {
  return new Promise((resolve, reject) => {
    if (window.google?.accounts?.id) {
      resolve();
      return;
    }

    const existing = document.querySelector('script[data-google-identity]');

    if (existing) {
      existing.addEventListener('load', resolve);
      existing.addEventListener('error', reject);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = resolve;
    script.onerror = reject;
    document.body.appendChild(script);
  });
}

function isGoogleConfigured() {
  return Boolean(
    GOOGLE_CLIENT_ID &&
      GOOGLE_CLIENT_ID !== 'TU_CLIENT_ID_DE_GOOGLE' &&
      GOOGLE_CLIENT_ID.trim().length > 20
  );
}

export default function Login({ onLogin, theme = 'light', setTheme }) {
  const googleButtonRef = useRef(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  
  // NUEVO: Estado para guardar el rol seleccionado antes del login
  const [selectedRole, setSelectedRole] = useState('student'); // 'student' o 'teacher'

  const googleReady = isGoogleConfigured();
  const isDark = theme === 'dark';

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  useEffect(() => {
    window.__cyberlabGoogleLoginCallback = async (response) => {
      try {
        setLoading(true);
        setError('');

        const result = await api.loginWithGoogle(response.credential);
        
        // Inyectamos el rol seleccionado al objeto de usuario
        const userData = { ...result.user, role: selectedRole };

        localStorage.setItem('cyberlab_user', JSON.stringify(userData));
        localStorage.setItem('cyberlab_token', result.token);
        localStorage.setItem('cyberlab_session_token', result.token);

        onLogin(userData);
      } catch (err) {
        console.error(err);
        setError(
          err.message ||
            'No fue posible iniciar sesión. Verifica que estés usando tu cuenta institucional.'
        );
      } finally {
        setLoading(false);
      }
    };
  }, [onLogin, selectedRole]); // Añadimos selectedRole a las dependencias

  useEffect(() => {
    let cancelled = false;

    async function initGoogle() {
      try {
        if (!googleReady) return;

        await loadGoogleScript();

        if (cancelled) return;

        if (!window.google?.accounts?.id) {
          setError('No se pudo inicializar Google Identity Services.');
          return;
        }

        if (window.__cyberlabGoogleInitializedFor !== GOOGLE_CLIENT_ID) {
          window.google.accounts.id.initialize({
            client_id: GOOGLE_CLIENT_ID,
            callback: (response) => {
              window.__cyberlabGoogleLoginCallback?.(response);
            },
          });

          window.__cyberlabGoogleInitializedFor = GOOGLE_CLIENT_ID;
        }

        if (googleButtonRef.current) {
          googleButtonRef.current.innerHTML = '';

          window.google.accounts.id.renderButton(googleButtonRef.current, {
            theme: isDark ? 'filled_black' : 'outline',
            size: 'large',
            text: 'signin_with',
            shape: 'pill',
            logo_alignment: 'left',
            width: 360,
          });
        }
      } catch (err) {
        console.error(err);
        setError('No se pudo cargar el acceso con Google.');
      }
    }

    initGoogle();

    return () => {
      cancelled = true;
    };
  }, [googleReady, isDark, selectedRole]); // Re-renderizar si cambia el rol

  function toggleTheme() {
    setTheme?.(isDark ? 'light' : 'dark');
  }

  // NUEVO: Función para saltarse Google durante el desarrollo
  function handleDevLogin() {
    const mockUser = {
      id: selectedRole === 'teacher' ? 'profesor-local' : 'student-local-01',
      email: selectedRole === 'teacher' ? 'profesor@correounivalle.edu.co' : 'estudiante@correounivalle.edu.co',
      name: selectedRole === 'teacher' ? 'Profesor CyberLab' : 'Estudiante Demo',
      role: selectedRole
    };
    
    localStorage.setItem('cyberlab_user', JSON.stringify(mockUser));
    localStorage.setItem('cyberlab_token', 'dev-token-secret');
    onLogin(mockUser);
  }

  return (
    <main className={`login-page-modern ${isDark ? 'dark' : 'light'}`}>
      <button className="login-theme-toggle" onClick={toggleTheme} type="button">
        {isDark ? <Sun size={18} /> : <Moon size={18} />}
        <span>{isDark ? 'Modo claro' : 'Modo oscuro'}</span>
      </button>

      <section className="login-left-panel">
        <div className="login-brand-modern featured">
          <div className="login-logo-modern">
            <ShieldCheck size={38} />
          </div>

          <div>
            <strong>CyberLab</strong>
            <span>Simulador académico de ciberseguridad</span>
          </div>
        </div>

        <div className="login-hero-copy minimal">
          <span className="login-eyebrow">
            <GraduationCap size={16} />
            Plataforma académica
          </span>

          <h1>
            Aprende y evalúa ciberseguridad en entornos controlados
          </h1>

          <p>
            Accede como estudiante para resolver escenarios prácticos o como docente para evaluar el desempeño y revisar evidencias cualitativas.
          </p>
        </div>

        <div className="login-feature-row">
          <div>
            <TerminalSquare size={19} />
            <span>Laboratorios Docker</span>
          </div>

          <div>
            <Activity size={19} />
            <span>Checkpoints y Evidencias</span>
          </div>

          <div>
            <ShieldCheck size={19} />
            <span>Acceso institucional</span>
          </div>
        </div>
      </section>

      <section className="login-card-modern compact">
        <div className="login-card-top">
          <span className="institution-badge">
            <ShieldCheck size={14} />
            Universidad del Valle
          </span>

          <h2>Iniciar sesión</h2>
          <p>Selecciona tu rol e ingresa con tu cuenta institucional.</p>
        </div>

        {/* NUEVO: Selector de Roles */}
        <div style={{ display: 'flex', gap: '10px', marginBottom: '20px', width: '100%', maxWidth: '360px', margin: '0 auto 20px auto' }}>
          <button 
            type="button"
            onClick={() => setSelectedRole('student')}
            style={{ flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', border: `2px solid ${selectedRole === 'student' ? '#2ea043' : '#30363d'}`, borderRadius: '8px', background: selectedRole === 'student' ? '#2ea04315' : 'transparent', color: 'inherit', cursor: 'pointer', transition: '0.2s' }}
          >
            <User size={24} color={selectedRole === 'student' ? '#2ea043' : '#8b949e'} />
            <strong style={{ fontSize: '14px' }}>Estudiante</strong>
          </button>
          
          <button 
            type="button"
            onClick={() => setSelectedRole('teacher')}
            style={{ flex: 1, padding: '12px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', border: `2px solid ${selectedRole === 'teacher' ? '#1f6feb' : '#30363d'}`, borderRadius: '8px', background: selectedRole === 'teacher' ? '#1f6feb15' : 'transparent', color: 'inherit', cursor: 'pointer', transition: '0.2s' }}
          >
            <Users size={24} color={selectedRole === 'teacher' ? '#1f6feb' : '#8b949e'} />
            <strong style={{ fontSize: '14px' }}>Docente</strong>
          </button>
        </div>

        <div className="login-google-area">
          {googleReady ? (
            <div className="google-button-wrapper modern" ref={googleButtonRef} />
          ) : (
            <div className="google-pending-card modern" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
              <div style={{ textAlign: 'center', marginBottom: '15px' }}>
                <strong>Modo Desarrollo Local</strong>
                <p>Google Auth no configurado. Usa el ingreso temporal para avanzar.</p>
              </div>
              <button 
                onClick={handleDevLogin}
                style={{ width: '100%', padding: '12px', background: selectedRole === 'teacher' ? '#1f6feb' : '#2ea043', color: 'white', border: 'none', borderRadius: '6px', fontWeight: 'bold', cursor: 'pointer' }}
              >
                Entrar como {selectedRole === 'teacher' ? 'Docente' : 'Estudiante'} (Dev)
              </button>
            </div>
          )}
        </div>

        {loading && (
          <div className="login-loading-modern">
            <span className="loader-dot" />
            Validando tu cuenta...
          </div>
        )}

        {error && (
          <div className="login-error-modern">
            {error}
          </div>
        )}

        <div className="login-bottom-note minimal" style={{ marginTop: '30px' }}>
          <LockKeyhole size={18} />
          <p>
            El acceso está restringido a usuarios autorizados de la Universidad del Valle.
          </p>
        </div>
      </section>
    </main>
  );
}