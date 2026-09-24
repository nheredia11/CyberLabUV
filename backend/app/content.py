from __future__ import annotations

from typing import Any
from .schemas import CatalogItem, ModuleDetail, CheckpointDef

MOCK_CATALOG = [
    {
        "id": "S01",
        "title": "Reconocimiento de Red y Escaneo de Servicios",
        "description": "Descubrimiento activo de hosts y enumeración de puertos usando Nmap.",
        "category": "network",
        "difficulty": "beginner",
        "estimated_hours": 2,
        "route": "/modules/s01",
        "active": True,
        "theory": (
            "### Fundamentación Teórica\n\n"
            "El reconocimiento de red es la fase inicial de cualquier auditoría de seguridad o prueba de penetración. "
            "Su objetivo es identificar direcciones IP activas, puertos TCP/UDP abiertos y versiones de servicios ejecutándose en el objetivo.\n\n"
            "**Mapeo de Marcos de Reference:**\n"
            "- **MITRE ATT&CK:** T1595 (Active Scanning) y T1046 (Network Service Discovery).\n"
            "- **Objetivo:** Comprender la superficie de ataque expuesta por una infraestructura."
        ),
        "checkpoints": [
            {
                "id": "s01_cp1",
                "title": "Identificación de Puertos Abiertos",
                "type": "flag",
                "question": "Ejecuta un escaneo Nmap e indica qué puerto TCP no estándar está abierto en el contenedor objetivo.",
                "points": 10,
            },
            {
                "id": "s01_cp2",
                "title": "Detección de Servicios y Versiones",
                "type": "flag",
                "question": "Determina el nombre y la versión exacta del servicio web que escucha en el objetivo.",
                "points": 15,
            },
            {
                "id": "s01_cp3",
                "title": "Obtención de la Flag del Encabezado",
                "type": "flag",
                "question": "Ingresa la flag oculta en la respuesta HTTP Server banner.",
                "points": 25,
            },
        ],
    },
    {
        "id": "S02",
        "title": "Vulnerabilidades en Autenticación HTTP",
        "description": "Análisis y explotación de mecanismos deficientes de autenticación web.",
        "category": "web",
        "difficulty": "intermediate",
        "estimated_hours": 3,
        "route": "/modules/s02",
        "active": True,
        "theory": (
            "### Fundamentación Teórica\n\n"
            "Los errores en la validación de identidad permiten a atacantes suplantar usuarios legítimos o eludir esquemas "
            "de control de acceso HTTP Básico o basados en formularios sin cifrado o bloqueos adecuados.\n\n"
            "**Mapeo de Marcos de Referencia:**\n"
            "- **OWASP Top 10:** A07:2021 – Identification and Authentication Failures.\n"
            "- **MITRE ATT&CK:** T1110 (Brute Force).\n"
            "- **Objetivo:** Comprender los riesgos de contraseñas débiles y canales no autenticados."
        ),
        "checkpoints": [
            {
                "id": "s02_cp1",
                "title": "Identificación del Esquema de Autenticación",
                "type": "flag",
                "question": "¿Qué método de autenticación utiliza la aplicación objetivo (ej. Basic Auth, Form)?",
                "points": 10,
            },
            {
                "id": "s02_cp2",
                "title": "Ataque de Diccionario / Fuerza Bruta",
                "type": "flag",
                "question": "Obtén la contraseña válida para el usuario 'admin' mediante un diccionario de prueba.",
                "points": 20,
            },
            {
                "id": "s02_cp3",
                "title": "Acceso al Panel y Flag de Administración",
                "type": "flag",
                "question": "Ingresa la flag obtenida tras ingresar exitosamente al panel administrativo.",
                "points": 20,
            },
        ],
    },
    {
        "id": "S03",
        "title": "Explotación Web OWASP (SQLi y XSS)",
        "description": "Inyección de código SQL y Cross-Site Scripting en aplicaciones vulnerables.",
        "category": "web",
        "difficulty": "intermediate",
        "estimated_hours": 4,
        "route": "/modules/s03",
        "active": True,
        "theory": (
            "### Fundamentación Teórica\n\n"
            "Las fallas de inyección ocurren cuando datos no confiables son enviados a un intérprete como parte de un comando o consulta. "
            "Por su parte, XSS permite a los atacantes ejecutar scripts en el navegador de la víctima.\n\n"
            "**Mapeo de Marcos de Referencia:**\n"
            "- **OWASP Top 10:** A03:2021 – Injection.\n"
            "- **MITRE ATT&CK:** T1190 (Exploit Public-Facing Application).\n"
            "- **Objetivo:** Evaluar el impacto de la falta de sanitización de entradas en la capa web."
        ),
        "checkpoints": [
            {
                "id": "s03_cp1",
                "title": "Bypass de Autenticación vía SQLi",
                "type": "flag",
                "question": "Inyecta una sentencia SQL en el formulario de inicio de sesión para eludir la autenticación.",
                "points": 20,
            },
            {
                "id": "s03_cp2",
                "title": "Ejecución de Cross-Site Scripting (XSS)",
                "type": "flag",
                "question": "Consigue ejecutar un script en el navegador e ingresa el token reflejado.",
                "points": 20,
            },
            {
                "id": "s03_cp3",
                "title": "Extracción de la Flag de la Base de Datos",
                "type": "flag",
                "question": "Extrae el valor del registro secreto oculto en la tabla 'flags' de la base de datos.",
                "points": 25,
            },
        ],
    },
    {
        "id": "S04",
        "title": "Seguridad en Servicios Remotos (SSH y FTP)",
        "description": "Auditoría e inspección de autenticación en protocolos SSH y FTP.",
        "category": "system",
        "difficulty": "intermediate",
        "estimated_hours": 3,
        "route": "/modules/s04",
        "active": True,
        "theory": (
            "### Fundamentación Teórica\n\n"
            "Los servicios de administración remota como SSH y la transferencia de archivos por FTP suelen ser blanco de "
            "ataques de adivinación de credenciales o configuraciones inseguras (como accesos anónimos habilitados).\n\n"
            "**Mapeo de Marcos de Referencia:**\n"
            "- **MITRE ATT&CK:** T1021 (Remote Services) y T1110.001 (Password Cracking).\n"
            "- **Objetivo:** Configurar y auditar la fortaleza de accesos a infraestructura de servidores."
        ),
        "checkpoints": [
            {
                "id": "s04_cp1",
                "title": "Inspección de FTP Anónimo",
                "type": "flag",
                "question": "Accede al servidor FTP expuesto y descarga el archivo con la flag de reconocimiento.",
                "points": 15,
            },
            {
                "id": "s04_cp2",
                "title": "Ataque de Diccionario sobre SSH",
                "type": "flag",
                "question": "Obtén el password del usuario 'student' para el servicio SSH.",
                "points": 20,
            },
            {
                "id": "s04_cp3",
                "title": "Flag en el Sistema de Archivos Remoto",
                "type": "flag",
                "question": "Inicia sesión mediante SSH y lee el contenido del archivo /home/student/flag.txt.",
                "points": 20,
            },
        ],
    },
    {
        "id": "S05",
        "title": "Intercepción de Tráfico y Man-in-the-Middle (MITM)",
        "description": "Análisis de tráfico no cifrado en redes locales mediante Wireshark o tcpdump.",
        "category": "network",
        "difficulty": "advanced",
        "estimated_hours": 4,
        "route": "/modules/s05",
        "active": True,
        "theory": (
            "### Fundamentación Teórica\n\n"
            "La falta de cifrado en la capa de transporte (HTTP, FTP, Telnet) permite a un atacante con acceso al "
            "segmento de red interceptar, leer y modificar tramas de datos en tránsito sin que los extremos se percaten.\n\n"
            "**Mapeo de Marcos de Referencia:**\n"
            "- **MITRE ATT&CK:** T1557 (Adversary-in-the-Middle).\n"
            "- **Objetivo:** Comprender la necesidad del uso obligatorio de protocolos seguros (HTTPS/TLS)."
        ),
        "checkpoints": [
            {
                "id": "s05_cp1",
                "title": "Captura de Paquetes de Red",
                "type": "flag",
                "question": "Captura el tráfico entre la víctima y el servidor e identifica el protocolo no seguro utilizado.",
                "points": 15,
            },
            {
                "id": "s05_cp2",
                "title": "Extracción de Credenciales en Claro",
                "type": "flag",
                "question": "Analiza las cargas útiles (payloads) de los paquetes HTTP/FTP para extraer el usuario interceptado.",
                "points": 20,
            },
            {
                "id": "s05_cp3",
                "title": "Flag Interceptada en Tráfico",
                "type": "flag",
                "question": "Ingresa la flag de la sesión transmitida en texto claro a través de la red.",
                "points": 25,
            },
        ],
    },
]


def load_module(module_id: str) -> ModuleDetail | None:
    for raw_item in MOCK_CATALOG:
        if raw_item["id"].upper() == module_id.upper():
            # Extraer y transformar checkpoints a instancias de CheckpointDef
            checkpoints_data = raw_item.get("checkpoints", [])
            checkpoints_objs = [CheckpointDef(**cp) for cp in checkpoints_data]
            
            # Construir dict sin la llave de checkpoints raw para pasárselo a ModuleDetail
            item_data = {k: v for k, v in raw_item.items() if k not in ("checkpoints", "theory")}
            
            return ModuleDetail(
                **item_data,
                theory=raw_item.get("theory", "Contenido teórico en preparación..."),
                checkpoints=checkpoints_objs,
            )
    return None


def load_catalog() -> list[CatalogItem]:
    items = []
    for raw_item in MOCK_CATALOG:
        # Filtrar llaves no pertenecientes a CatalogItem para instanciación limpia
        item_data = {
            k: v for k, v in raw_item.items() 
            if k in CatalogItem.model_fields
        }
        item = CatalogItem(**item_data)
        items.append(item)
    return items


def load_all_modules() -> list[ModuleDetail]:
    raw_modules = [load_module(item.id) for item in load_catalog()]
    modules = [m for m in raw_modules if m is not None]
    
    return sorted(
        modules, 
        key=lambda module: getattr(module, "orden", 0) if getattr(module, "orden", None) is not None else 0
    )