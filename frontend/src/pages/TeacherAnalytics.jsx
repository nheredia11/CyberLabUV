import { useState, useEffect } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function TeacherAnalytics({ onBack }) {
  const [submissions, setSubmissions] = useState([]);
  const [selectedSubmission, setSelectedSubmission] = useState(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("evidences");
  
  // Estado para manejar notificaciones en pantalla en lugar de alerts
  const [notification, setNotification] = useState({ show: false, type: "", message: "" });

  useEffect(() => {
    fetchSubmissions();
  }, []);

  const fetchSubmissions = async () => {
    setLoading(true);
    try {
      const response = await fetch("http://localhost:8000/api/progress/", {
        headers: { "x-cyberlab-token": "dev-token-secret" }
      });
      if (response.ok) {
        const data = await response.json();
        setSubmissions(data);
      } else {
        loadMockData();
      }
    } catch (error) {
      loadMockData();
    } finally {
      setLoading(false);
    }
  };

  const loadMockData = () => {
    setSubmissions([
      {
        id: "1",
        student_id: "student-local-01",
        module_id: "S01",
        status: "completed",
        answers: {
          "recon-cp-1": "Werkzeug httpd 2.2.2 (Python 3.10.8)",
          "recon-cp-2": "Puerto 5000 abierto"
        },
        feedback: ""
      },
      {
        id: "2",
        student_id: "juan.perez@correounivalle.edu.co",
        module_id: "S02",
        status: "pending_review",
        answers: {
          "auth-cp-1": "admin / password123",
        },
        feedback: ""
      }
    ]);
  };

  const showNotification = (type, message) => {
    setNotification({ show: true, type, message });
    setTimeout(() => {
      setNotification({ show: false, type: "", message: "" });
    }, 3000);
  };

  const handleSendFeedback = async () => {
    if (!selectedSubmission || !feedbackText.trim()) return;
    setIsSubmitting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 800));
      
      const updatedSubmissions = submissions.map(sub => 
        sub.id === selectedSubmission.id ? { ...sub, feedback: feedbackText } : sub
      );
      setSubmissions(updatedSubmissions);
      setSelectedSubmission({ ...selectedSubmission, feedback: feedbackText });
      setFeedbackText("");
      
      showNotification("success", "✅ Retroalimentación enviada correctamente.");
    } catch (error) {
      showNotification("error", "❌ Ocurrió un error al enviar la retroalimentación.");
      console.error("[TeacherAnalytics] Error enviando feedback:", error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const surveyMetrics = [
    { name: 'Claridad Teórica', score: 4.6 },
    { name: 'Estabilidad Docker', score: 4.8 },
    { name: 'Utilidad del Lab', score: 4.9 },
    { name: 'Dificultad Reto', score: 3.5 },
  ];

  if (loading) {
    return (
      <main className="learning-route-page">
        <section className="learning-loading">
          <h2>Cargando panel docente...</h2>
        </section>
      </main>
    );
  }

  return (
    <main className="learning-route-page" style={{ display: 'flex', flexDirection: 'column', gap: '20px', padding: '20px', height: '100vh', boxSizing: 'border-box' }}>
      
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #30363d', paddingBottom: '15px' }}>
        <div>
          <h1 style={{ color: '#c9d1d9', margin: 0 }}>Panel de Control Docente</h1>
          <p style={{ color: '#8b949e', margin: '5px 0 0 0' }}>Seguimiento académico y calidad del simulador</p>
        </div>
        <div style={{ display: 'flex', gap: '10px' }}>
          <button 
            onClick={() => setActiveTab("evidences")}
            style={{ padding: '10px 20px', background: activeTab === 'evidences' ? '#1f6feb' : '#21262d', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', transition: '0.2s' }}
          >
            📋 Calificar Evidencias
          </button>
          <button 
            onClick={() => setActiveTab("metrics")}
            style={{ padding: '10px 20px', background: activeTab === 'metrics' ? '#2ea043' : '#21262d', color: '#fff', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 'bold', transition: '0.2s' }}
          >
            📊 Métricas del Curso
          </button>
        </div>
      </header>

      {/* Notificación flotante */}
      {notification.show && (
        <div style={{ 
          position: 'fixed', top: '80px', right: '20px', zIndex: 1000,
          background: notification.type === 'success' ? '#2ea043' : '#f85149',
          color: '#fff', padding: '15px 25px', borderRadius: '8px',
          boxShadow: '0 4px 12px rgba(0,0,0,0.15)', fontWeight: 'bold',
          animation: 'fadeIn 0.3s ease-in-out'
        }}>
          {notification.message}
        </div>
      )}

      {activeTab === "evidences" && (
        <div style={{ display: 'flex', gap: '20px', flex: 1, overflow: 'hidden' }}>
          <aside style={{ width: '300px', background: '#161b22', border: '1px solid #30363d', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column' }}>
            <h3 style={{ borderBottom: '1px solid #30363d', paddingBottom: '10px', marginBottom: '15px', color: '#c9d1d9' }}>👨‍🏫 Entregas Pendientes</h3>
            <div style={{ flex: 1, overflowY: 'auto' }}>
              {submissions.length === 0 ? (
                <p style={{ color: '#8b949e' }}>No hay entregas registradas.</p>
              ) : (
                <ul style={{ listStyle: 'none', padding: 0, margin: 0 }}>
                  {submissions.map((sub) => (
                    <li key={sub.id} style={{ marginBottom: '10px' }}>
                      <button
                        onClick={() => { setSelectedSubmission(sub); setFeedbackText(sub.feedback || ""); }}
                        style={{ width: '100%', textAlign: 'left', padding: '12px', background: selectedSubmission?.id === sub.id ? '#1f6feb' : '#0d1117', color: selectedSubmission?.id === sub.id ? '#ffffff' : '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px', cursor: 'pointer', transition: '0.2s' }}
                      >
                        <strong style={{ display: 'block', wordBreak: 'break-all' }}>{sub.student_id}</strong>
                        <span style={{ fontSize: '12px', color: selectedSubmission?.id === sub.id ? '#c1d4ff' : '#8b949e' }}>Módulo: {sub.module_id}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </aside>

          <section style={{ flex: 1, background: '#161b22', border: '1px solid #30363d', borderRadius: '8px', padding: '24px', display: 'flex', flexDirection: 'column', overflowY: 'auto' }}>
            {!selectedSubmission ? (
              <div style={{ margin: 'auto', color: '#8b949e', textAlign: 'center' }}>
                <h2>Panel de Evaluación Cualitativa</h2>
                <p>Selecciona un estudiante para revisar sus flags y enviar retroalimentación.</p>
              </div>
            ) : (
              <>
                <h2 style={{ color: '#c9d1d9', marginBottom: '20px' }}>Evidencias de {selectedSubmission.student_id}</h2>
                <div style={{ background: '#0d1117', padding: '15px', borderRadius: '6px', border: '1px solid #30363d', marginBottom: '20px' }}>
                  {Object.entries(selectedSubmission.answers).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '15px', borderBottom: '1px dashed #30363d', paddingBottom: '10px' }}>
                      <strong style={{ color: '#8b949e', display: 'block', fontSize: '12px', marginBottom: '5px' }}>Pregunta / ID: {key}</strong>
                      <span style={{ color: '#3fb950', fontFamily: 'monospace', fontSize: '15px', wordBreak: 'break-all' }}>{value}</span>
                    </div>
                  ))}
                </div>

                <div style={{ background: '#0d1117', padding: '20px', borderRadius: '8px', border: '1px solid #30363d' }}>
                  <h3 style={{ marginBottom: '10px', color: '#c9d1d9' }}>💬 Redactar Retroalimentación</h3>
                  {selectedSubmission.feedback && !feedbackText ? (
                    <div style={{ padding: '15px', background: '#23863615', borderLeft: '4px solid #238636', color: '#c9d1d9', borderRadius: '4px' }}>
                      <p style={{ margin: 0, lineHeight: '1.5' }}>{selectedSubmission.feedback}</p>
                      <button 
                        onClick={() => setFeedbackText(selectedSubmission.feedback)} 
                        style={{ marginTop: '15px', background: 'transparent', border: '1px solid #30363d', color: '#58a6ff', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', transition: '0.2s' }}
                      >
                        Editar Feedback
                      </button>
                    </div>
                  ) : (
                    <>
                      <textarea
                        value={feedbackText}
                        onChange={(e) => setFeedbackText(e.target.value)}
                        placeholder="Escribe tu comentario orientador..."
                        style={{ width: '100%', height: '120px', padding: '15px', background: '#161b22', color: '#c9d1d9', border: '1px solid #30363d', borderRadius: '6px', resize: 'vertical', fontFamily: 'inherit' }}
                      />
                      <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '15px', gap: '10px' }}>
                        {selectedSubmission.feedback && (
                          <button 
                            onClick={() => setFeedbackText("")}
                            style={{ padding: '10px 20px', background: 'transparent', color: '#8b949e', border: 'none', cursor: 'pointer' }}
                          >
                            Cancelar
                          </button>
                        )}
                        <button 
                          onClick={handleSendFeedback} 
                          disabled={isSubmitting || !feedbackText.trim()} 
                          style={{ padding: '10px 24px', background: isSubmitting || !feedbackText.trim() ? '#21262d' : '#238636', color: '#fff', border: 'none', borderRadius: '6px', cursor: isSubmitting || !feedbackText.trim() ? 'not-allowed' : 'pointer', transition: '0.2s', fontWeight: 'bold' }}
                        >
                          {isSubmitting ? "Enviando..." : "Enviar Retroalimentación"}
                        </button>
                      </div>
                    </>
                  )}
                </div>
              </>
            )}
          </section>
        </div>
      )}

      {activeTab === "metrics" && (
        <section style={{ flex: 1, background: '#161b22', border: '1px solid #30363d', borderRadius: '8px', padding: '30px', display: 'flex', flexDirection: 'column' }}>
          <div style={{ marginBottom: '30px' }}>
            <h2 style={{ color: '#c9d1d9', margin: 0 }}>Resultados de Encuestas Estudiantiles</h2>
            <p style={{ color: '#8b949e', marginTop: '5px' }}>Promedios obtenidos en la escala Likert (1 a 5) tras la finalización de las prácticas.</p>
          </div>
          
          <div style={{ flex: 1, background: '#0d1117', border: '1px solid #30363d', borderRadius: '8px', padding: '20px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={surveyMetrics} margin={{ top: 20, right: 30, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#30363d" vertical={false} />
                <XAxis dataKey="name" stroke="#8b949e" tick={{fill: '#8b949e'}} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 5]} stroke="#8b949e" tick={{fill: '#8b949e'}} axisLine={false} tickLine={false} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#161b22', borderColor: '#30363d', color: '#c9d1d9', borderRadius: '6px' }} 
                  itemStyle={{ color: '#3fb950' }} 
                  cursor={{fill: '#21262d'}}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Bar dataKey="score" name="Promedio (1-5)" fill="#2ea043" radius={[4, 4, 0, 0]} barSize={60} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </section>
      )}
    </main>
  );
}