import os
import logging
import re
from sib_api_v3_sdk import Configuration, ApiClient, TransactionalEmailsApi, SendSmtpEmail
from sib_api_v3_sdk.rest import ApiException

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('BREVO_API_KEY')
        self.sender_email = os.environ.get('BREVO_SENDER_EMAIL')
        self.sender_name = os.environ.get('BREVO_SENDER_NAME', 'Visual Outlet')

    def _get_api_instance(self):
        config = Configuration()
        config.api_key['api-key'] = self.api_key
        return TransactionalEmailsApi(ApiClient(config))

    def enviar_codigo_verificacion(self, correo: str, nombre: str, codigo: str) -> bool:
        html = f"""
        <div style="font-family: Arial; padding: 20px;">
            <h2>Hola {nombre}</h2>
            <p>Tu código de verificación es:</p>
            <div style="font-size: 32px; letter-spacing: 5px; padding: 15px; background: #f0f0ff;">
                <strong>{codigo}</strong>
            </div>
            <p>Expira en 15 minutos.</p>
        </div>
        """
        return self._enviar_correo(correo, nombre, "Código de verificación", html, asincrono=True)

    def enviar_codigo_reset(self, correo: str, nombre: str, codigo: str) -> bool:
        html = f"""
        <div style="font-family: Arial; padding: 20px;">
            <h2>Restablecer contraseña</h2>
            <p>Hola {nombre}, tu código es:</p>
            <div style="font-size: 32px; letter-spacing: 5px; padding: 15px; background: #fff5f0;">
                <strong>{codigo}</strong>
            </div>
            <p>Expira en 15 minutos.</p>
        </div>
        """
        return self._enviar_correo(correo, nombre, "Restablecer contraseña", html, asincrono=False)

    def _enviar_correo(self, email: str, nombre: str, asunto: str, html: str, asincrono: bool) -> bool:
        if os.environ.get('FLASK_ENV') == 'development' and not self.api_key:
            print(f"\n📧 SIMULADO: {email} - Código: {self._extraer_codigo(html)}\n")
            return True

        if not self.api_key or not self.sender_email:
            logger.error("Brevo no configurado")
            return False

        def enviar():
            try:
                api = self._get_api_instance()
                email_obj = SendSmtpEmail(
                    to=[{"email": email, "name": nombre}],
                    sender={"name": self.sender_name, "email": self.sender_email},
                    subject=asunto,
                    html_content=html
                )
                api.send_transac_email(email_obj)
                logger.info(f"✅ Email enviado a {email}")
                return True
            except Exception as e:
                logger.error(f"❌ Error: {e}")
                return False

        if asincrono:
            import threading
            threading.Thread(target=enviar, daemon=True).start()
            return True
        return enviar()

    def _extraer_codigo(self, html: str) -> str:
        match = re.search(r'(\d{6})', html)
        return match.group(1) if match else '??????'


email_service = EmailService()

def enviar_codigo_verificacion(correo, nombre, codigo):
    return email_service.enviar_codigo_verificacion(correo, nombre, codigo)

def enviar_codigo_reset(correo, nombre, codigo):
    return email_service.enviar_codigo_reset(correo, nombre, codigo)