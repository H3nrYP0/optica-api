import os
import base64
import re
import json
from flask import Blueprint, request, jsonify
import anthropic

# ============================================================
# Blueprint para verificación de comprobantes con Claude Vision
# ============================================================

comprobante_bp = Blueprint("comprobante", __name__, url_prefix="/pedidos")

# ---------- VALIDACIÓN DE API KEY ----------
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    raise RuntimeError(
        "❌ ANTHROPIC_API_KEY no configurada. "
        "Agrega la variable de entorno o en tu .env"
    )
client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ---------- CONFIGURACIÓN ----------
TIPOS_VALIDOS = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_TAMANO = 10 * 1024 * 1024  # 10 MB

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

# ---------- FUNCIÓN AUXILIAR ----------
def _parse_claude_response(text: str) -> dict:
    """Limpia y parsea el JSON devuelto por Claude."""
    clean = re.sub(r"^```json\s*", "", text.strip(), flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean).strip()
    try:
        return json.loads(clean)
    except json.JSONDecodeError:
        match = re.search(r"\{[\s\S]+\}", clean)
        if match:
            return json.loads(match.group())
        raise ValueError("No se pudo extraer JSON de la respuesta de Claude")

# ---------- ENDPOINT PRINCIPAL ----------
@comprobante_bp.route("/verificar-comprobante", methods=["POST"])
def verificar_comprobante():
    # 1. Validar que llegue el archivo
    if "comprobante" not in request.files:
        return jsonify({"error": "No se recibió ningún archivo."}), 400

    archivo = request.files["comprobante"]
    mime = archivo.mimetype

    # 2. Validar tipo de archivo
    if mime not in TIPOS_VALIDOS:
        return jsonify({
            "error": "Formato no soportado. Sube JPG, PNG, WEBP o GIF."
        }), 400

    # 3. Validar montoEsperado
    monto_esperado = request.form.get("montoEsperado")
    if not monto_esperado:
        return jsonify({"error": "Falta el parámetro montoEsperado."}), 400

    # 4. Leer y validar tamaño
    contenido = archivo.read()
    if len(contenido) > MAX_TAMANO:
        return jsonify({"error": "El archivo supera los 10 MB."}), 400

    # 5. Convertir a base64
    b64 = base64.b64encode(contenido).decode("utf-8")

    # 6. Llamar a Claude Vision
    try:
        message = client.messages.create(
            model="claude-3-haiku-20240307",  # ← Modelo válido y económico
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
        return jsonify({"error": f"Error al contactar Claude: {str(e)}"}), 502
    except Exception as e:
        return jsonify({"error": f"Error inesperado: {str(e)}"}), 500

    # 7. Procesar respuesta de Claude
    raw = "".join(block.text for block in message.content if hasattr(block, "text"))
    try:
        datos = _parse_claude_response(raw)
    except (ValueError, json.JSONDecodeError):
        return jsonify({
            "error": "No se pudo interpretar el comprobante. Sube una imagen más clara."
        }), 422

    # 8. Normalizar tipos y agregar coincidencia
    datos["monto"] = int(datos.get("monto", -1))
    datos["confianza"] = int(datos.get("confianza", 0))
    datos["coincide"] = (datos["monto"] == int(monto_esperado))

    return jsonify(datos), 200