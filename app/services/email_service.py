import os
import logging
import re
from flask_mail import Mail, Message
from flask import current_app

logger = logging.getLogger(__name__)

# Instancia global de Mail
mail = Mail()

def init_mail(app):
    """Inicializa Mailtrap en la app Flask"""
    app.config.update(
        MAIL_SERVER=os.environ.get('MAIL_SERVER', 'sandbox.smtp.mailtrap.io'),
        MAIL_PORT=int(os.environ.get('MAIL_PORT', 2525)),
        MAIL_USE_TLS=os.environ.get('MAIL_USE_TLS', 'True') == 'True',
        MAIL_USE_SSL=os.environ.get('MAIL_USE_SSL', 'False') == 'True',
        MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
        MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
        MAIL_DEFAULT_SENDER=os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@visualoutlet.com')
    )
    mail.init_app(app)


class EmailService:
    def __init__(self):
        self.sender_email = os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@visualoutlet.com')
        self.modo_simulado = os.environ.get('FLASK_ENV') == 'development'

    def enviar_codigo_verificacion(self, correo: str, nombre: str, codigo: str) -> bool:
        """Envía código de verificación usando Mailtrap"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a1a2e;">¡Hola {nombre}!</h2>
            <p>Gracias por registrarte en <strong>Visual Outlet</strong>.</p>
            <p>Tu código de verificación es:</p>
            <div style="background: #f0f0ff; padding: 15px; text-align: center; font-size: 32px; letter-spacing: 5px; border-radius: 8px;">
                <strong>{codigo}</strong>
            </div>
            <p style="color: #666;">Este código expira en <strong>15 minutos</strong>.</p>
            <hr>
            <p style="color: #999; font-size: 11px;">Si no solicitaste este registro, ignora este mensaje.</p>
        </body>
        </html>
        """
        
        if self.modo_simulado:
            print(f"\n{'='*60}")
            print(f"📧 [MAILTRAP SIMULADO] Código de verificación")
            print(f"   Para: {correo} ({nombre})")
            print(f"   Código: {codigo}")
            print(f"   Link para ver: https://sandbox.mailtrap.io/inboxes")
            print(f"{'='*60}\n")
            return True
        
        return self._enviar_correo(correo, nombre, "🔐 Código de verificación — Visual Outlet", html)

    def enviar_codigo_reset(self, correo: str, nombre: str, codigo: str) -> bool:
        """Envía código de recuperación usando Mailtrap"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #1a1a2e;">Restablecer contraseña</h2>
            <p>Hola <strong>{nombre}</strong>,</p>
            <p>Recibimos una solicitud para restablecer tu contraseña.</p>
            <p>Usa este código:</p>
            <div style="background: #fff5f0; padding: 15px; text-align: center; font-size: 32px; letter-spacing: 5px; border-radius: 8px;">
                <strong>{codigo}</strong>
            </div>
            <p style="color: #666;">Expira en <strong>15 minutos</strong>.</p>
            <hr>
            <p style="color: #999; font-size: 11px;">Si no solicitaste este cambio, ignora este mensaje.</p>
        </body>
        </html>
        """
        
        if self.modo_simulado:
            print(f"\n{'='*60}")
            print(f"📧 [MAILTRAP SIMULADO] Código de recuperación")
            print(f"   Para: {correo} ({nombre})")
            print(f"   Código: {codigo}")
            print(f"   Link para ver: https://sandbox.mailtrap.io/inboxes")
            print(f"{'='*60}\n")
            return True
        
        return self._enviar_correo(correo, nombre, "🔑 Restablecer contraseña — Visual Outlet", html)

    def _enviar_correo(self, email: str, nombre: str, asunto: str, html: str) -> bool:
        """Envía correo real usando Flask-Mail con Mailtrap"""
        try:
            msg = Message(
                subject=asunto,
                recipients=[email],
                html=html,
                sender=self.sender_email
            )
            mail.send(msg)
            logger.info(f"✅ Correo enviado a {email} via Mailtrap")
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando correo a {email}: {str(e)}")
            return False


# Instancia global
email_service = EmailService()

# Funciones de conveniencia
def enviar_codigo_verificacion(correo, nombre, codigo):
    return email_service.enviar_codigo_verificacion(correo, nombre, codigo)

def enviar_codigo_reset(correo, nombre, codigo):
    return email_service.enviar_codigo_reset(correo, nombre, codigo)