import React, { useState, useEffect } from 'react';
import { api } from '../lib/api.js';

export default function ConsentModal({ userId, onConsentAccepted }) {
  const [hasConsent, setHasConsent] = useState(true);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/consent', {
      headers: { 'Authorization': `Bearer ${localStorage.getItem('cyberlab_token')}` }
    })
      .then(res => res.json())
      .then(data => {
        if (!data.accepted) {
          setHasConsent(false);
        } else {
          setHasConsent(true);
          if (onConsentAccepted) onConsentAccepted();
        }
      })
      .catch(() => setHasConsent(false))
      .finally(() => setLoading(false));
  }, []);

  async function handleAccept() {
    try {
      const res = await fetch('http://localhost:8000/api/consent', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('cyberlab_token')}`
        },
        body: JSON.stringify({ accepted: true, version: "1.0" })
      });
      if (res.ok) {
        setHasConsent(true);
        if (onConsentAccepted) onConsentAccepted();
      }
    } catch (e) {
      console.error("Error al guardar consentimiento", e);
    }
  }

  if (loading || hasConsent) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
      <div className="w-full max-w-lg rounded-2xl bg-gray-900 border border-gray-800 p-6 text-white shadow-2xl">
        <h2 className="text-xl font-bold text-cyan-400 mb-3">Consentimiento Informado - CyberLabUV</h2>
        <div className="space-y-3 text-sm text-gray-300 max-h-60 overflow-y-auto pr-2 mb-6">
          <p><strong>Objetivo del estudio:</strong> Evaluar la efectividad pedagógica y técnica de la plataforma CyberLabUV en la enseñanza práctica de ciberseguridad.</p>
          <p><strong>Datos que se guardan:</strong> Se recopilarán registros de progreso en checkpoints, interacciones en terminales de contenedores Docker y respuestas anónimas a encuestas Likert.</p>
          <p><strong>Participación voluntaria:</strong> Su participación es completamente voluntaria y no afectará sus calificaciones académicas ordinarias.</p>
          <p><strong>Derecho a retiro:</strong> Puede suspender su uso o retirar su participación en cualquier momento sin penalización alguna.</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={handleAccept}
            className="flex-1 rounded-xl bg-cyan-600 hover:bg-cyan-500 py-2.5 font-medium transition-colors"
          >
            Aceptar y Continuar
          </button>
          <button
            onClick={() => alert("Debe aceptar el consentimiento para utilizar los módulos interactivos.")}
            className="flex-1 rounded-xl bg-gray-800 hover:bg-gray-700 py-2.5 font-medium text-gray-400 transition-colors"
          >
            No aceptar
          </button>
        </div>
      </div>
    </div>
  );
}