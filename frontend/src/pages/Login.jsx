import { useEffect, useRef, useState } from 'react';
import {
  ShieldCheck,
  GraduationCap,
  LockKeyhole,
  Activity,
  Mail,
  Loader2,
  Info,
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

export default function Login({ onLogin }) {
  const googleButtonRef = useRef(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const googleReady = isGoogleConfigured();

  useEffect(() => {
    async function initGoogle() {
      try {
        if (!googleReady) return;

        await loadGoogleScript();

        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: async (response) => {
            try {
              setLoading(true);
              setError('');

              const result = await api.loginGoogle(response.credential);

              localStorage.setItem('cyberlab_user', JSON.stringify(result.user));
              localStorage.setItem('cyberlab_token', result.token);

              onLogin(result.user);
            } catch (err) {
              console.error(err);
              setError(err.message || 'No fue posible iniciar sesión. Verifica que uses tu cuenta institucional.');
            } finally {
              setLoading(false);
            }
          },
        });

        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: 'outline',
          size: 'large',
          text: 'signin_with',
          shape: 'pill',
          logo_alignment: 'left',
          width: 320,
        });
      } catch (err) {
        console.error(err);
        setError('No se pudo cargar el acceso con Google.');
      }
    }

    initGoogle();
  }, [googleReady, onLogin]);

  return (
    <main className="login-page">
      <section className="login-hero">
        <div className="login-brand">
          <div className="login-logo">
            <ShieldCheck size={34} />
          </div>

          <div>
            <strong>CyberLab</strong>
            <span>Simulador académico de ciberseguridad</span>
          </div>
        </div>

        <h1>Entrenamiento práctico con laboratorios controlados</h1>

        <p>
          Accede con tu cuenta institucional para continuar tu ruta de aprendizaje,
          ejecutar escenarios locales, registrar evidencias y recibir retroalimentación.
        </p>

        <div className="login-features">
          <div>
            <GraduationCap size={20} />
            <span>Ruta por módulos</span>
          </div>

          <div>
            <LockKeyhole size={20} />
            <span>Acceso institucional</span>
          </div>

          <div>
            <Activity size={20} />
            <span>Analíticas formativas</span>
          </div>
        </div>
      </section>

      <section className="login-card">
        <span className="badge">Acceso Universidad del Valle</span>

        <h2>Iniciar sesión</h2>

        <p className="muted">
          Usa tu correo institucional para ingresar al laboratorio.
        </p>

        {googleReady ? (
          <div className="google-button-wrapper" ref={googleButtonRef} />
        ) : (
          <div className="google-pending-card">
            <div className="google-pending-icon">
              <Mail size={22} />
            </div>

            <div>
              <strong>Acceso institucional pendiente</strong>
              <p>
                Configura el Client ID de Google para habilitar el ingreso con
                cuentas institucionales.
              </p>
            </div>
          </div>
        )}

        {loading && (
          <div className="login-loading">
            <Loader2 size={18} className="spin" />
            Validando acceso institucional...
          </div>
        )}

        {error && (
          <div className="login-error">
            {error}
          </div>
        )}

        <div className="login-helper clean">
          <Info size={18} />
          <p>
            El acceso estará disponible únicamente para usuarios autorizados de la
            Universidad del Valle.
          </p>
        </div>
      </section>
    </main>
  );
}