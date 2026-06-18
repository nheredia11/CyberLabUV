from __future__ import annotations

import os
from datetime import datetime, timezone

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

ATTEMPTS: list[dict[str, str | bool]] = []

APP_TITLE = os.getenv("APP_TITLE", "CyberLabUV - Laboratorio de Autenticación HTTP")
DEMO_USER = os.getenv("DEMO_USER", "estudiante")
DEMO_PASSWORD = os.getenv("DEMO_PASSWORD", "laboratorio123")


def register_attempt(username: str, success: bool) -> None:
    ATTEMPTS.append(
        {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "username": username or "(vacío)",
            "success": success,
        }
    )

    if len(ATTEMPTS) > 25:
        del ATTEMPTS[0]


@app.get("/")
def index():
    return render_template(
        "index.html",
        app_title=APP_TITLE,
        attempts=list(reversed(ATTEMPTS)),
        demo_user=DEMO_USER,
    )


@app.post("/login")
def login():
    username = request.form.get("username", "")
    password = request.form.get("password", "")

    success = username == DEMO_USER and password == DEMO_PASSWORD

    register_attempt(username=username, success=success)

    message = (
        "Acceso concedido al entorno de demostración."
        if success
        else "Credenciales inválidas en el laboratorio controlado."
    )

    return render_template(
        "index.html",
        app_title=APP_TITLE,
        attempts=list(reversed(ATTEMPTS)),
        demo_user=DEMO_USER,
        last_message=message,
        last_success=success,
    )


@app.get("/attempts")
def attempts():
    return jsonify(
        {
            "total": len(ATTEMPTS),
            "items": list(reversed(ATTEMPTS)),
        }
    )


@app.get("/health")
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "auth-http-lab",
            "attempts": len(ATTEMPTS),
        }
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)