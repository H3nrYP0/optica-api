import bcrypt
import logging
from datetime import datetime
from flask_jwt_extended import create_access_token

# Logger de seguridad — registra eventos importantes
security_logger = logging.getLogger('security')
logging.basicConfig(level=logging.INFO)

def verificar_contrasenia(contrasenia_plana, contrasenia_guardada, usuario_id, db):
    """
    Verifica la contraseña del usuario.
    Si está en texto plano la encripta automáticamente.
    Retorna True si es válida, False si no.
    """
    # Ya está encriptada con bcrypt
    if contrasenia_guardada.startswith("$2b$") or contrasenia_guardada.startswith("$2a$"):
        return bcrypt.checkpw(
            contrasenia_plana.encode('utf-8'),
            contrasenia_guardada.encode('utf-8')
        )

    # Aún en texto plano — comparar y encriptar para el futuro
    if contrasenia_guardada == contrasenia_plana:
        hash_nuevo = bcrypt.hashpw(
            contrasenia_plana.encode('utf-8'),
            bcrypt.gensalt()
        )
        # Importar aquí para evitar imports circulares
        from app.Models.models import Usuario
        usuario = Usuario.query.get(usuario_id)
        usuario.contrasenia = hash_nuevo.decode('utf-8')
        db.session.commit()
        security_logger.info(
            f"🔐 Contraseña encriptada automáticamente: usuario_id={usuario_id}"
        )
        return True

    return False


def generar_token(usuario, permisos, nombre_rol):
    """
    Genera un JWT con los datos del usuario.
    El token contiene todo lo necesario para no consultar la BD en cada petición.
    """
    token_data = {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": nombre_rol,
        "rol_id": usuario.rol_id,
        "permisos": permisos,
    }

    return create_access_token(
        identity=str(usuario.id),
        additional_claims=token_data
    )


def log_login_exitoso(usuario_id, nombre_rol, ip):
    """Registra un login exitoso en los logs"""
    security_logger.info(
        f"✅ Login exitoso: usuario_id={usuario_id} | rol={nombre_rol} | IP={ip} | {datetime.now()}"
    )


def log_login_fallido(motivo, correo, ip):
    """Registra un intento de login fallido en los logs"""
    security_logger.warning(
        f"⚠️  Login fallido - {motivo}: {correo} | IP={ip} | {datetime.now()}"
    )


def log_cuenta_inactiva(correo, ip):
    """Registra intento de login con cuenta inactiva"""
    security_logger.warning(
        f"⚠️  Login bloqueado - cuenta inactiva: {correo} | IP={ip} | {datetime.now()}"
    )