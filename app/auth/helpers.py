# app/auth/helpers.py
import logging
from datetime import datetime
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token

# ─────────────────────────────────────────────
# Logger de seguridad
# ─────────────────────────────────────────────
security_logger = logging.getLogger('security')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
)


def verificar_contrasenia(contrasenia_plana: str, contrasenia_guardada: str, usuario_id: int, db) -> bool:
    """
    Verifica la contraseña del usuario contra el hash almacenado.
    """
    try:
        resultado = check_password_hash(contrasenia_guardada, contrasenia_plana)
        if resultado:
            security_logger.info(f"🔐 Contraseña verificada OK: usuario_id={usuario_id}")
        else:
            security_logger.warning(f"🔐 Contraseña incorrecta: usuario_id={usuario_id}")
        return resultado
    except Exception as e:
        security_logger.error(f"❌ Error verificando contraseña usuario_id={usuario_id}: {e}")
        return False


def generar_token(usuario, permisos: list, nombre_rol: str) -> str:
    """
    Genera el JWT con todos los datos necesarios para autorización.
    """
    claims = {
        "id":       usuario.id,
        "nombre":   usuario.nombre,
        "correo":   usuario.correo,
        "rol":      nombre_rol.lower().strip() if nombre_rol else "usuario",
        "rol_id":   usuario.rol_id,
        "permisos": permisos,
    }

    return create_access_token(
        identity=str(usuario.id),
        additional_claims=claims
    )


def log_login_exitoso(usuario_id: int, nombre_rol: str, ip: str) -> None:
    security_logger.info(
        f"✅ Login OK | id={usuario_id} | rol={nombre_rol} | IP={ip} | {datetime.now().isoformat()}"
    )


def log_login_fallido(motivo: str, correo: str, ip: str) -> None:
    security_logger.warning(
        f"⚠️  Login FAIL | motivo={motivo} | correo={correo} | IP={ip} | {datetime.now().isoformat()}"
    )


def log_cuenta_inactiva(correo: str, ip: str) -> None:
    security_logger.warning(
        f"🚫 Login BLOCKED | cuenta inactiva | correo={correo} | IP={ip} | {datetime.now().isoformat()}"
    )