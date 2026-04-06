import bcrypt
import logging
from datetime import datetime
from flask_jwt_extended import create_access_token

# Logger de seguridad — registra eventos importantes
security_logger = logging.getLogger('security')
logging.basicConfig(level=logging.INFO)

def verificar_contrasenia(contrasenia_plana, contrasenia_guardada, usuario_id, db):
    """
    Verifica la contraseña. Si está en texto plano, la encripta.
    """
    # Verificación de hash bcrypt
    if contrasenia_guardada.startswith(("$2b$", "$2a$")):
        return bcrypt.checkpw(
            contrasenia_plana.encode('utf-8'),
            contrasenia_guardada.encode('utf-8')
        )

    # Autocorrección de texto plano a Hash
    if contrasenia_guardada == contrasenia_plana:
        hash_nuevo = bcrypt.hashpw(contrasenia_plana.encode('utf-8'), bcrypt.gensalt())
        from app.Models.models import Usuario
        usuario = Usuario.query.get(usuario_id)
        usuario.contrasenia = hash_nuevo.decode('utf-8')
        db.session.commit()
        security_logger.info(f"🔐 Password auto-hash: usuario_id={usuario_id}")
        return True
    return False

def generar_token(usuario, permisos, nombre_rol):
    """
    Genera el JWT. 
    IMPORTANTE: nombre_rol.lower() asegura que el decorador reconozca al 'dev'.
    """
    token_data = {
        "id": usuario.id,
        "nombre": usuario.nombre,
        "correo": usuario.correo,
        "rol": nombre_rol.lower() if nombre_rol else "", # Normalizado
        "rol_id": usuario.rol_id,
        "permisos": permisos, 
    }

    return create_access_token(
        identity=str(usuario.id),
        additional_claims=token_data
    )

def log_login_exitoso(usuario_id, nombre_rol, ip):
    security_logger.info(f"✅ Login OK: id={usuario_id} | rol={nombre_rol} | IP={ip} | {datetime.now()}")

def log_login_fallido(motivo, correo, ip):
    security_logger.warning(f"⚠️ Login FAIL - {motivo}: {correo} | IP={ip} | {datetime.now()}")

def log_cuenta_inactiva(correo, ip):
    security_logger.warning(f"⚠️ Login BLOCK - Inactiva: {correo} | IP={ip} | {datetime.now()}")