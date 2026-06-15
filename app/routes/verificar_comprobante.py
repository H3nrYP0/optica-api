# =============================================================
# verificar_comprobante.py
#
# Endpoint Python para verificar comprobantes de pago con Claude Vision.
# Soluciona el error CORS: el navegador no puede llamar a
# api.anthropic.com directamente. Este endpoint corre en tu
# servidor, recibe la imagen y devuelve el monto leído.
#
# ── INSTALACIÓN ──────────────────────────────────────────────
#   pip install anthropic python-multipart
#
# ── VARIABLE DE ENTORNO (en Render → Environment) ────────────
#   ANTHROPIC_API_KEY = sk-ant-xxxxxxxxxxxxxxxx
#
# ══════════════════════════════════════════════════════════════
# OPCIÓN A — FastAPI  (si tu backend usa FastAPI)
# ══════════════════════════════════════════════════════════════
# MONTAJE en tu main.py / app.py:
#
#   from verificar_comprobante import router as comprobante_router
#   app.include_router(comprobante_router)
#
# El frontend llama a: POST /pedidos/verificar-comprobante
# ─────────────────────────────────────────────────────────────

import os
import base64
import json
import re

import anthropic

# ── Soporte FastAPI ───────────────────────────────────────────
try:
    from fastapi import APIRouter, UploadFile, File, Form, HTTPException
    from fastapi.responses import JSONResponse

    router = APIRouter(prefix="/pedidos", tags=["pedidos"])

    ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    TIPOS_VALIDOS = {
        "image/jpeg", "image/png", "image/webp", "image/gif"
    }

    PROMPT = """Eres un sistema de verificación de comprobantes bancarios colombianos (Bancolombia, Nequi, Daviplata).

Analiza esta imagen con máxima precisión y extrae:

1. MONTO TRANSFERIDO exacto:
   - Busca: "Valor", "Total", "Transferencia por", "Transferiste", "Pagaste", "Monto"
   - Lee CADA dígito sin redondear
   - "$99.000" -> 99000 | "$149.500" -> 149500 | "$1.250.000" -> 1250000
   - Los puntos son separadores de miles, la coma es decimal

2. NOMBRE del remitente (quien envía)

Responde SOLO con este JSON exacto, sin texto extra ni markdown:
{"monto": <entero sin puntos ni comas>, "montoTexto": "<como aparece>", "remitente": "<nombre>", "confianza": <1-10>}

Si no puedes leer el monto con certeza -> monto: -1"""

    def _parse_ocr_response(text: str) -> dict:
        """Parsea la respuesta de Claude limpiando posibles ```json ... ```"""
        clean = re.sub(r"^```json\s*", "", text.strip(), flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]+\}", clean)
            if match:
                return json.loads(match.group())
            raise ValueError("No se pudo parsear respuesta OCR")

    @router.post("/verificar-comprobante")
    async def verificar_comprobante(
        comprobante: UploadFile = File(...),
        montoEsperado: str = Form(...),
    ):
        # Validar tipo
        if comprobante.content_type not in TIPOS_VALIDOS:
            raise HTTPException(
                status_code=400,
                detail="Formato no soportado. Sube una imagen JPG, PNG, WEBP o GIF."
            )

        # Leer archivo y convertir a base64
        contenido = await comprobante.read()
        if len(contenido) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="El archivo supera los 10 MB.")

        b64 = base64.b64encode(contenido).decode("utf-8")
        mime = comprobante.content_type

        # Llamar a Claude Vision (server-side, sin CORS)
        try:
            message = client.messages.create(
                model="claude-haiku-4-5-20251001",  # modelo rápido y económico para OCR
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": PROMPT},
                    ],
                }],
            )
        except anthropic.APIError as e:
            raise HTTPException(
                status_code=502,
                detail=f"Error al contactar Claude: {str(e)}"
            )

        raw = "".join(
            block.text for block in message.content
            if hasattr(block, "text")
        )

        try:
            datos = _parse_ocr_response(raw)
        except (ValueError, json.JSONDecodeError):
            raise HTTPException(
                status_code=502,
                detail="No se pudo interpretar el comprobante. Sube una imagen más clara."
            )

        # Asegurar tipos correctos
        datos["monto"]     = int(datos.get("monto", -1))
        datos["confianza"] = int(datos.get("confianza", 0))

        return JSONResponse(content=datos)

except ImportError:
    # FastAPI no instalado — ignorar, usar Flask abajo
    pass


# ══════════════════════════════════════════════════════════════
# OPCIÓN B — Flask  (si tu backend usa Flask)
# ══════════════════════════════════════════════════════════════
# MONTAJE en tu app.py / __init__.py:
#
#   from verificar_comprobante import comprobante_bp
#   app.register_blueprint(comprobante_bp)
#
# El frontend llama a: POST /pedidos/verificar-comprobante
# ─────────────────────────────────────────────────────────────

try:
    from flask import Blueprint, request, jsonify

    comprobante_bp = Blueprint("comprobante", __name__, url_prefix="/pedidos")

    ANTHROPIC_API_KEY_FLASK = os.environ.get("ANTHROPIC_API_KEY", "")
    client_flask = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY_FLASK)

    TIPOS_VALIDOS_FLASK = {
        "image/jpeg", "image/png", "image/webp", "image/gif"
    }

    PROMPT_FLASK = """Eres un sistema de verificación de comprobantes bancarios colombianos (Bancolombia, Nequi, Daviplata).

Analiza esta imagen con máxima precisión y extrae:

1. MONTO TRANSFERIDO exacto:
   - Busca: "Valor", "Total", "Transferencia por", "Transferiste", "Pagaste", "Monto"
   - Lee CADA dígito sin redondear
   - "$99.000" -> 99000 | "$149.500" -> 149500 | "$1.250.000" -> 1250000
   - Los puntos son separadores de miles, la coma es decimal

2. NOMBRE del remitente (quien envía)

Responde SOLO con este JSON exacto, sin texto extra ni markdown:
{"monto": <entero sin puntos ni comas>, "montoTexto": "<como aparece>", "remitente": "<nombre>", "confianza": <1-10>}

Si no puedes leer el monto con certeza -> monto: -1"""

    def _parse_flask(text: str) -> dict:
        clean = re.sub(r"^```json\s*", "", text.strip(), flags=re.IGNORECASE)
        clean = re.sub(r"\s*```$", "", clean).strip()
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            match = re.search(r"\{[\s\S]+\}", clean)
            if match:
                return json.loads(match.group())
            raise ValueError("No se pudo parsear respuesta OCR")

    @comprobante_bp.route("/verificar-comprobante", methods=["POST"])
    def verificar_comprobante_flask():
        if "comprobante" not in request.files:
            return jsonify({"error": "No se recibió ningún archivo."}), 400

        archivo = request.files["comprobante"]
        mime    = archivo.mimetype

        if mime not in TIPOS_VALIDOS_FLASK:
            return jsonify({"error": "Formato no soportado. Sube JPG, PNG, WEBP o GIF."}), 400

        contenido = archivo.read()
        if len(contenido) > 10 * 1024 * 1024:
            return jsonify({"error": "El archivo supera los 10 MB."}), 400

        b64 = base64.b64encode(contenido).decode("utf-8")

        try:
            message = client_flask.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=300,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": mime,
                                "data": b64,
                            },
                        },
                        {"type": "text", "text": PROMPT_FLASK},
                    ],
                }],
            )
        except anthropic.APIError as e:
            return jsonify({"error": f"Error al contactar Claude: {str(e)}"}), 502

        raw = "".join(
            block.text for block in message.content
            if hasattr(block, "text")
        )

        try:
            datos = _parse_flask(raw)
        except (ValueError, json.JSONDecodeError):
            return jsonify({"error": "No se pudo interpretar el comprobante. Sube una imagen más clara."}), 502

        datos["monto"]     = int(datos.get("monto", -1))
        datos["confianza"] = int(datos.get("confianza", 0))

        return jsonify(datos), 200

except ImportError:
    # Flask no instalado — ignorar
    pass
