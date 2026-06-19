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

        localStorage.setItem('cyberlab_user', JSON.stringify(result.user));
        localStorage.setItem('cyberlab_token', result.token);
        localStorage.setItem('cyberlab_session_token', result.token);

        onLogin(result.user);
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
  }, [onLogin]);

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
  }, [googleReady, isDark]);

  function toggleTheme() {
    setTheme?.(isDark ? 'light' : 'dark');
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
            Plataforma académica de práctica
          </span>

          <h1>
            Aprende ciberseguridad practicando en entornos controlados
          </h1>

          <p>
            Accede a escenarios guiados, registra evidencias de tu práctica y revisa
            tu progreso dentro de una ruta de aprendizaje diseñada para apoyar el
            curso de ciberseguridad.
          </p>
        </div>

        <div className="login-feature-row">
          <div>
            <TerminalSquare size={19} />
            <span>Laboratorios reproducibles</span>
          </div>

          <div>
            <Activity size={19} />
            <span>Seguimiento del progreso</span>
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

          <p>
            Ingresa con tu cuenta institucional para continuar tu ruta de aprendizaje.
          </p>
        </div>

        <div className="login-google-area">
          {googleReady ? (
            <div className="google-button-wrapper modern" ref={googleButtonRef} />
          ) : (
            <div className="google-pending-card modern">
              <div>
                <strong>Acceso institucional en configuración</strong>
                <p>
                  Falta configurar el Client ID de Google para habilitar el ingreso.
                </p>
              </div>
            </div>
          )}
        </div>

        {loading && (
          <div className="login-loading-modern">
            <span className="loader-dot" />
            Validando tu cuenta institucional...
          </div>
        )}

        {error && (
          <div className="login-error-modern">
            {error}
          </div>
        )}

        <div className="login-security-list minimal">
          <div>
            <CheckCircle2 size={17} />
            <span>Validación con cuenta institucional.</span>
          </div>

          <div>
            <CheckCircle2 size={17} />
            <span>Progreso asociado al estudiante.</span>
          </div>

          <div>
            <CheckCircle2 size={17} />
            <span>Prácticas guiadas en ambiente controlado.</span>
          </div>
        </div>

        <div className="login-bottom-note minimal">
          <LockKeyhole size={18} />
          <p>
            El acceso está restringido a usuarios autorizados de la Universidad del Valle.
          </p>
        </div>

        <div className="login-card-footer">
          <span>CyberLab</span>
          <ArrowRight size={16} />
        </div>
      </section>
    </main>
  );
}