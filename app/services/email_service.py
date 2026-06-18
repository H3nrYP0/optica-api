import os
import smtplib
import logging
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('EMAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('EMAIL_PORT', 587))
        self.sender_email = os.environ.get('EMAIL_USER')
        self.sender_password = os.environ.get('EMAIL_PASSWORD')
        self.use_tls = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'

        if not self.sender_email or not self.sender_password:
            logger.warning("EMAIL_USER o EMAIL_PASSWORD no configurados. El envío fallará.")
        else:
            logger.info("EmailService inicializado con Gmail SMTP")

    def _enviar_con_reintentos(self, destinatario: str, nombre: str, asunto: str, html: str, max_intentos: int = 3) -> bool:
        """Intenta enviar el correo hasta max_intentos veces (síncrono)."""
        for intento in range(1, max_intentos + 1):
            try:
                # Crear mensaje
                msg = MIMEMultipart('alternative')
                msg['From'] = f"Visual Outlet <{self.sender_email}>"
                msg['To'] = destinatario
                msg['Subject'] = asunto

                parte_html = MIMEText(html, 'html')
                msg.attach(parte_html)

                # Conectar y enviar (timeout 15 segundos)
                if self.use_tls:
                    server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
                    server.starttls()
                else:
                    server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)

                server.login(self.sender_email, self.sender_password)
                server.sendmail(self.sender_email, destinatario, msg.as_string())
                server.quit()

                logger.info(f"✅ Correo enviado a {destinatario} (intento {intento})")
                return True

            except Exception as e:
                logger.warning(f"⚠️ Intento {intento} falló para {destinatario}: {e}")
                if intento < max_intentos:
                    time.sleep(2)  # espera 2 segundos antes de reintentar

        logger.error(f"❌ Todos los intentos fallaron para {destinatario}")
        return False

    def enviar_codigo_verificacion(self, correo: str, nombre: str, codigo: str) -> bool:
        print(f"📧 [VERIFICACIÓN] Código para {correo}: {codigo}")
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center" style="padding:40px 20px;">
                <table width="560" cellpadding="0" cellspacing="0"
                       style="background:#fff;border-radius:8px;overflow:hidden;
                              box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                  <tr>
                    <td style="background:#1a1a2e;padding:28px 40px;">
                      <h1 style="margin:0;color:#fff;font-size:22px;">Visual Outlet</h1>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:40px;">
                      <h2 style="margin:0 0 12px;color:#1a1a2e;">Hola, {nombre} 👋</h2>
                      <p style="margin:0 0 28px;color:#555;font-size:15px;line-height:1.6;">
                        Tu código de verificación es (caduca en <strong>15 minutos</strong>):
                      </p>
                      <div style="text-align:center;margin:0 0 32px;">
                        <span style="display:inline-block;background:#f0f0ff;
                                     border:2px dashed #5b5fc7;border-radius:10px;
                                     padding:18px 48px;font-size:36px;font-weight:700;
                                     letter-spacing:12px;color:#3730a3;">
                          {codigo}
                        </span>
                      </div>
                      <p style="margin:0;color:#999;font-size:13px;">
                        Si no solicitaste este registro, ignora este mensaje.
                      </p>
                    </td>
                  </tr>
                  <tr>
                    <td style="background:#f8f8f8;padding:20px 40px;
                               border-top:1px solid #eee;text-align:center;">
                      <p style="margin:0;color:#bbb;font-size:12px;">
                        © 2025 Visual Outlet · Correo automático, no responder.
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """
        return self._enviar_con_reintentos(correo, nombre, "Código de verificación — Visual Outlet", html)

    def enviar_codigo_reset(self, correo: str, nombre: str, codigo: str) -> bool:
        print(f"📧 [RESET] Código para {correo}: {codigo}")
        html = f"""
        <!DOCTYPE html>
        <html lang="es">
        <body style="margin:0;padding:0;background:#f5f5f5;font-family:Arial,sans-serif;">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td align="center" style="padding:40px 20px;">
                <table width="560" cellpadding="0" cellspacing="0"
                       style="background:#fff;border-radius:8px;overflow:hidden;
                              box-shadow:0 2px 8px rgba(0,0,0,0.08);">
                  <tr>
                    <td style="background:#1a1a2e;padding:28px 40px;">
                      <h1 style="margin:0;color:#fff;font-size:22px;">Visual Outlet</h1>
                    </td>
                  </tr>
                  <tr>
                    <td style="padding:40px;">
                      <h2 style="margin:0 0 12px;color:#1a1a2e;">Restablecer contraseña</h2>
                      <p style="margin:0 0 8px;color:#555;font-size:15px;line-height:1.6;">
                        Hola <strong>{nombre}</strong>, tu código es
                        (caduca en <strong>15 minutos</strong>):
                      </p>
                      <div style="text-align:center;margin:0 0 32px;">
                        <span style="display:inline-block;background:#fff5f0;
                                     border:2px dashed #ea580c;border-radius:10px;
                                     padding:18px 48px;font-size:36px;font-weight:700;
                                     letter-spacing:12px;color:#c2410c;">
                          {codigo}
                        </span>
                      </div>
                      <p style="margin:0;color:#999;font-size:13px;">
                        Si no solicitaste este cambio, ignora este mensaje.
                      </p>
                    </td>
                  </tr>
                  <tr>
                    <td style="background:#f8f8f8;padding:20px 40px;
                               border-top:1px solid #eee;text-align:center;">
                      <p style="margin:0;color:#bbb;font-size:12px;">
                        © 2025 Visual Outlet · Correo automático, no responder.
                      </p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """
        return self._enviar_con_reintentos(correo, nombre, "Restablecer contraseña — Visual Outlet", html)


# Instancia única (compatible con imports actuales)
email_service = EmailService()

def enviar_codigo_verificacion(correo, nombre, codigo):
    return email_service.enviar_codigo_verificacion(correo, nombre, codigo)

def enviar_codigo_reset(correo, nombre, codigo):
    return email_service.enviar_codigo_reset(correo, nombre, codigo)