"""
Capa de análisis por IA. Se usa SOLO cuando una app no está en la base de
datos curada. Devuelve siempre un JSON estructurado y deja explícito que
es una estimación (no un dato verificado), tal como se explica en la UI.

Usa la API de Google Gemini (free tier, sin tarjeta de crédito).
Conseguir API key gratis en: https://aistudio.google.com/apikey
"""

import json
import logging
import os

import requests

logger = logging.getLogger(__name__)

GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

SYSTEM_PROMPT = """Sos un asistente experto en seguridad digital infantil.
Tu tarea es estimar, para una app/web/plataforma que te van a nombrar,
un análisis de riesgo orientado a padres y adolescentes en Argentina.

Basate en el tipo de funcionalidades típicas de esa plataforma (chat con
desconocidos, contenido generado por usuarios, geolocalización, compras
in-app, algoritmos de recomendación, etc.), sin inventar datos específicos
que no puedas justificar razonablemente.

Respondé EXCLUSIVAMENTE con un JSON válido, sin texto adicional, sin
backticks de markdown, con esta forma exacta:

{
  "existe": true,
  "edad_recomendada": 13,
  "nivel_riesgo": "medio",
  "factores_riesgo": ["Contacto con desconocidos", "Compras in-app"],
  "justificacion": "Explicación breve en 2-3 oraciones.",
  "confianza": "media"
}

Reglas:
- "nivel_riesgo" debe ser uno de: "bajo", "medio", "alto", "muy_alto".
- "confianza" debe ser uno de: "baja", "media", "alta".
- "factores_riesgo" es una lista de máximo 5 strings cortos.
- Si el nombre no corresponde a ninguna app/web/plataforma real o
  identificable, devolvé {"existe": false}.
- No agregues ningún texto fuera del JSON.
"""


class AIAnalysisError(Exception):
    pass


def analizar_app_con_ia(nombre_app: str) -> dict:
    """
    Llama a la API de Gemini para estimar el riesgo de una app que no
    está en la base curada. Lanza AIAnalysisError si algo falla.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise AIAnalysisError(
            "No hay GEMINI_API_KEY configurada en el entorno."
        )

    payload = {
        "system_instruction": {"parts": [{"text": SYSTEM_PROMPT}]},
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": f'Analizá la siguiente app/web/plataforma: "{nombre_app}"'}
                ],
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
            "maxOutputTokens": 500,
            "responseMimeType": "application/json",
        },
    }
    headers = {"content-type": "application/json"}
    params = {"key": api_key}

    try:
        response = requests.post(
            GEMINI_API_URL, headers=headers, params=params, json=payload, timeout=20
        )
        response.raise_for_status()
    except requests.RequestException as exc:
        logger.warning("Error llamando a la API de Gemini: %s", exc)
        raise AIAnalysisError("No se pudo contactar al servicio de IA.") from exc

    data = response.json()
    try:
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError) as exc:
        logger.warning("Respuesta de Gemini con forma inesperada: %s", data)
        raise AIAnalysisError("La IA devolvió una respuesta no válida.") from exc

    if raw_text.startswith("```"):
        raw_text = raw_text.strip("`")
        if raw_text.lower().startswith("json"):
            raw_text = raw_text[4:]
        raw_text = raw_text.strip()

    try:
        result = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        logger.warning("Respuesta de IA no parseable como JSON: %s", raw_text)
        raise AIAnalysisError("La IA devolvió una respuesta no válida.") from exc

    return result