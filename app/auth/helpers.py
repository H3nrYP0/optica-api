import logging
from datetime import datetime
from werkzeug.security import check_password_hash
from flask_jwt_extended import create_access_token

security_logger = logging.getLogger('security')

def verificar_contrasenia(contrasenia_plana: str, contrasenia_guardada: str, usuario_id: int) -> bool:
    """Verifica la contraseña y loguea el resultado."""
    try:
        resultado = check_password_hash(contrasenia_guardada, contrasenia_plana)
        if resultado:
            security_logger.info(f" Contraseña OK: usuario_id={usuario_id}")
        else:
            security_logger.warning(f" Contraseña INCORRECTA: usuario_id={usuario_id}")
        return resultado
    except Exception as e:
        security_logger.error(f"❌ Error en verificación (user {usuario_id}): {e}")
        return False

def generar_token(usuario, permisos: list, nombre_rol: str) -> str:
    """Genera JWT con claims de identidad, rol y permisos."""
    claims = {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": nombre_rol.lower().strip() if nombre_rol else "usuario",
        "rol_id": usuario.rol_id,
        "permisos": permisos,
    }
    return create_access_token(
        identity=str(usuario.id),
        additional_claims=claims
    )

def log_login_exitoso(usuario_id: int, nombre_rol: str, ip: str) -> None:
    security_logger.info(f"✅ Login OK | ID={usuario_id} | Rol={nombre_rol} | IP={ip}")

def log_login_fallido(motivo: str, correo: str, ip: str) -> None:
    security_logger.warning(f"⚠️ Login FAIL | Motivo={motivo} | Correo={correo} | IP={ip}")

def log_cuenta_inactiva(correo: str, ip: str) -> None:
    security_logger.warning(f"🚫 Login BLOCKED | Inactivo | Correo={correo} | IP={ip}")