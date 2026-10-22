import React, { useState, useEffect } from 'react';
import api from '../lib/api';

export default function ConsentModal({ onConsentAccepted }) {
  const [show, setShow] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    checkConsent();
  }, []);

  const checkConsent = async () => {
    try {
      const res = await api.get('/api/consent');
      if (!res.data.accepted) {
        setShow(true);
      } else if (onConsentAccepted) {
        onConsentAccepted();
      }
    } catch (err) {
      console.error("Error al verificar consentimiento", err);
    }
  };

  const handleAccept = async () => {
    setLoading(true);
    setError(null);
    try {
      await api.post('/api/consent', { accepted: true, version: '1.0' });
      setShow(false);
      if (onConsentAccepted) onConsentAccepted();
    } catch (err) {
      setError("No se pudo registrar el consentimiento. Inténtalo de nuevo.");
    } finally {
      setLoading(false);
    }
  };

  if (!show) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-70 backdrop-blur-sm p-4">
      <div className="bg-slate-900 border border-slate-700 rounded-xl max-w-lg w-full p-6 text-slate-100 shadow-2xl">
        <h2 className="text-xl font-bold text-cyan-400 mb-3">Consentimiento Informado - CyberLabUV</h2>
        <div className="text-sm text-slate-300 space-y-3 max-h-60 overflow-y-auto pr-2 mb-4 border-b border-slate-800 pb-3">
          <p><strong>Objetivo del estudio:</strong> Evaluar la efectividad pedagógica y técnica del simulador académico de ciberseguridad CyberLabUV en entornos prácticos controlados.</p>
          <p><strong>Datos que se guardan:</strong> Se registrarán únicamente los avances en los checkpoints de los laboratorios, marcas de tiempo de conexión y las respuestas anonimizadas a las encuestas de retroalimentación técnica y pedagógica.</p>
          <p><strong>Participación voluntaria:</strong> Su participación es completamente voluntaria. Ninguna decisión académica está atada a su participación en este estudio piloto.</p>
          <p><strong>Derecho a retirarse:</strong> Puede dejar de usar la plataforma o retirar sus datos en cualquier momento sin penalización alguna.</p>
        </div>
        {error && <p className="text-red-400 text-xs mb-3">{error}</p>}
        <div className="flex justify-end space-x-3">
          <button
            disabled={loading}
            onClick={handleAccept}
            className="bg-cyan-600 hover:bg-cyan-500 text-white px-5 py-2 rounded-lg font-medium transition"
          >
            {loading ? "Guardando..." : "Aceptar y Continuar"}
          </button>
        </div>
      </div>
    </div>
  );
}