from __future__ import annotations

import os
import socket
import threading
from datetime import datetime, timezone

from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

SCENARIO_ID = os.getenv("SCENARIO_ID", "S00")
LAB_MODE = os.getenv("LAB_MODE", "generic")
APP_TITLE = os.getenv("APP_TITLE", "CyberLab - Laboratorio académico")
DEMO_USER = os.getenv("DEMO_USER", "estudiante")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "laboratorio123")

EVENTS: list[dict[str, str | bool]] = []
COMMENTS: list[str] = []


SCENARIO_META = {
    "recon": {
        "badge": "Reconocimiento",
        "headline": "Mapa inicial de servicios expuestos",
        "summary": "Explora servicios visibles dentro de una red Docker controlada y registra hallazgos sin tocar sistemas externos.",
        "primary": "Identificar superficie de exposición",
        "risk": "Servicios innecesarios o mal inventariados",
        "control": "Inventario, segmentación y monitoreo",
        "steps": [
            "Abrir el laboratorio local.",
            "Observar servicios disponibles.",
            "Consultar eventos generados.",
            "Registrar hallazgos y controles."
        ],
        "cards": [
            ("Red controlada", "Todos los servicios pertenecen al laboratorio local."),
            ("Servicios simulados", "HTTP, SSH y FTP se representan de forma segura."),
            ("Evidencia", "El estudiante registra puertos, banners y eventos visibles.")
        ],
    },
    "auth_http": {
        "badge": "Autenticación HTTP",
        "headline": "Prueba controlada de autenticación débil",
        "summary": "Analiza intentos válidos y fallidos en una aplicación web local, sin usar credenciales reales.",
        "primary": "Comprender autenticación débil",
        "risk": "Intentos repetidos sin bloqueo progresivo",
        "control": "Bloqueo, MFA, logs y alertas",
        "steps": [
            "Realizar un intento fallido.",
            "Realizar un intento válido.",
            "Revisar eventos registrados.",
            "Proponer controles de mitigación."
        ],
        "cards": [
            ("Usuario de laboratorio", "Usa únicamente credenciales de demostración."),
            ("Eventos visibles", "Cada intento queda registrado para análisis."),
            ("Cierre pedagógico", "El foco está en comprender el riesgo, no en atacar sistemas reales.")
        ],
    },
    "web_owasp": {
        "badge": "OWASP Web",
        "headline": "Entradas inseguras en aplicación web",
        "summary": "Practica con formularios controlados para discutir inyección, XSS y Directory Traversal.",
        "primary": "Analizar validación de entradas",
        "risk": "Entradas no validadas o no sanitizadas",
        "control": "Validación, sanitización y autorización",
        "steps": [
            "Probar búsqueda didáctica.",
            "Enviar comentario de laboratorio.",
            "Solicitar archivo controlado.",
            "Proponer mitigaciones web."
        ],
        "cards": [
            ("Inyección", "Entrada de búsqueda con comportamiento didáctico."),
            ("XSS controlado", "Comentarios renderizados para discutir sanitización."),
            ("Traversal", "Solicitud de archivos con detección de patrones inseguros.")
        ],
    },
    "auth_services": {
        "badge": "SSH / FTP",
        "headline": "Autenticación simulada en servicios de red",
        "summary": "Observa intentos de autenticación válidos y fallidos sobre servicios simulados.",
        "primary": "Estudiar credenciales débiles",
        "risk": "Servicios expuestos con autenticación deficiente",
        "control": "MFA, llaves SSH, bloqueo y monitoreo",
        "steps": [
            "Seleccionar SSH o FTP simulado.",
            "Enviar intento fallido.",
            "Enviar intento válido.",
            "Registrar controles recomendados."
        ],
        "cards": [
            ("Simulación segura", "No levanta SSH ni FTP reales del sistema."),
            ("Eventos", "Los intentos quedan registrados como evidencia."),
            ("Defensa", "Permite discutir bloqueo, MFA y monitoreo.")
        ],
    },
    "mitm": {
        "badge": "MITM simulado",
        "headline": "Riesgo de tráfico no cifrado",
        "summary": "Observa cómo un mensaje no cifrado puede quedar expuesto en una simulación académica.",
        "primary": "Comprender exposición de tráfico",
        "risk": "Comunicación sin cifrado",
        "control": "HTTPS/TLS y validación de certificados",
        "steps": [
            "Enviar mensaje de laboratorio.",
            "Observar evento registrado.",
            "Analizar riesgo de texto claro.",
            "Proponer mitigaciones."
        ],
        "cards": [
            ("No es MITM real", "No se intercepta tráfico del usuario ni de la red."),
            ("Flujo simulado", "El mensaje se registra para discusión pedagógica."),
            ("Mitigación", "Se enfatiza el uso de TLS, certificados y monitoreo.")
        ],
    },
    "generic": {
        "badge": "Laboratorio",
        "headline": "Entorno académico controlado",
        "summary": "Laboratorio local para prácticas de ciberseguridad con fines formativos.",
        "primary": "Aprendizaje aplicado",
        "risk": "Riesgo conceptual",
        "control": "Uso ético y controlado",
        "steps": ["Abrir laboratorio.", "Observar eventos.", "Registrar evidencia."],
        "cards": [
            ("Ética", "Uso restringido al laboratorio."),
            ("Evidencia", "Registro de resultados."),
            ("Cierre", "Retroalimentación académica.")
        ],
    },
}


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def meta() -> dict:
    return SCENARIO_META.get(LAB_MODE, SCENARIO_META["generic"])


def add_event(kind: str, message: str, success: bool | None = None) -> None:
    EVENTS.append(
        {
            "time": now(),
            "kind": kind,
            "message": message,
            "success": success if success is not None else "",
        }
    )

    if len(EVENTS) > 60:
        del EVENTS[0]


def banner_server(port: int, banner: str) -> None:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen(5)

    while True:
        client, address = server.accept()
        add_event("recon", f"Conexión recibida desde {address[0]}:{address[1]} en puerto interno {port}.")
        client.sendall((banner + "\r\n").encode("utf-8"))
        client.close()


def start_recon_services() -> None:
    services = [
        (2222, "SSH-2.0-CyberLab-Recon-Lab"),
        (2121, "220 CyberLab FTP mock service ready"),
    ]

    for port, banner in services:
        thread = threading.Thread(target=banner_server, args=(port, banner), daemon=True)
        thread.start()


if LAB_MODE == "recon":
    start_recon_services()


@app.get("/")
def index():
    return render_template(
        "index.html",
        scenario_id=SCENARIO_ID,
        lab_mode=LAB_MODE,
        app_title=APP_TITLE,
        meta=meta(),
        events=list(reversed(EVENTS)),
        comments=COMMENTS,
        demo_user=DEMO_USER,
        public_url=request.host_url.rstrip("/"),
    )


@app.get("/health")
def health():
    attempts = len([event for event in EVENTS if event["kind"] in {"auth_http", "auth"}])

    return jsonify(
        {
            "status": "ok",
            "service": "cyberlab-scenario",
            "scenario_id": SCENARIO_ID,
            "mode": LAB_MODE,
            "events": len(EVENTS),
            "attempts": attempts,
        }
    )


@app.get("/events")
def events():
    return jsonify({"items": list(reversed(EVENTS)), "total": len(EVENTS)})


@app.get("/attempts")
def attempts():
    filtered = [
        event for event in reversed(EVENTS)
        if event["kind"] in {"auth_http", "auth"}
    ]

    return jsonify(
        {
            "total": len(filtered),
            "items": filtered,
        }
    )


@app.post("/auth-http/login")
def auth_http_login():
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    success = username == DEMO_USER and password == DEMO_PASSWORD
    result = "válido" if success else "fallido"

    add_event(
        "auth_http",
        f"Intento HTTP {result} con usuario '{username or '(vacío)'}'.",
        success=success,
    )

    return redirect(url_for("index"))


@app.get("/web/search")
def web_search():
    query = request.args.get("q", "").strip()

    records = [
        {"id": 1, "name": "admin", "role": "docente"},
        {"id": 2, "name": "estudiante", "role": "aprendiz"},
        {"id": 3, "name": "auditor", "role": "observador"},
    ]

    if not query:
        result = []
    elif "'" in query or " or " in query.lower() or "1=1" in query:
        result = records
        add_event("web", "Consulta con patrón riesgoso detectado en búsqueda didáctica.")
    else:
        result = [item for item in records if query.lower() in item["name"].lower()]
        add_event("web", f"Búsqueda ejecutada con término '{query}'.")

    return jsonify(
        {
            "query": query,
            "results": result,
            "note": "Respuesta didáctica para analizar validación de entradas en entorno controlado.",
        }
    )


@app.post("/web/comment")
def web_comment():
    comment = request.form.get("comment", "").strip()

    if comment:
        COMMENTS.append(comment)
        add_event("web", "Comentario recibido para discusión de XSS controlado y sanitización.")

    return redirect(url_for("index"))


@app.get("/web/file")
def web_file():
    filename = request.args.get("name", "readme.txt").strip()

    allowed_files = {
        "readme.txt": "Archivo público de laboratorio.",
        "guia.txt": "Guía breve del escenario OWASP.",
        "logs.txt": "Registro didáctico sin datos reales.",
    }

    if ".." in filename or "/" in filename or "\\" in filename:
        add_event("web", "Intento de Directory Traversal detectado de forma controlada.")
        return jsonify(
            {
                "requested": filename,
                "blocked": True,
                "message": "Patrón de Directory Traversal detectado. En un sistema real podría exponer archivos sensibles.",
            }
        )

    add_event("web", f"Archivo solicitado: {filename}.")

    return jsonify(
        {
            "requested": filename,
            "blocked": False,
            "content": allowed_files.get(filename, "Archivo no encontrado en el laboratorio."),
        }
    )


@app.post("/auth/login")
def auth_login():
    service = request.form.get("service", "ssh").strip()
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "").strip()

    success = username == DEMO_USER and password == DEMO_PASSWORD
    result = "válido" if success else "fallido"

    add_event(
        "auth",
        f"Intento {result} sobre servicio {service.upper()} con usuario '{username or '(vacío)'}'.",
        success=success,
    )

    return redirect(url_for("index"))


@app.post("/mitm/send")
def mitm_send():
    sender = request.form.get("sender", "cliente").strip()
    message = request.form.get("message", "").strip()

    if message:
        add_event("mitm", f"Mensaje no cifrado observado: {sender} → servidor: {message}")

    return redirect(url_for("index"))


if __name__ == "__main__":
    add_event("system", f"Laboratorio {SCENARIO_ID} iniciado en modo {LAB_MODE}.")
    app.run(host="0.0.0.0", port=5000)