import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.smtp_server = os.environ.get('EMAIL_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.environ.get('EMAIL_PORT', 465))  # Cambio a 465 por defecto
        self.sender_email = os.environ.get('EMAIL_USER')
        self.sender_password = os.environ.get('EMAIL_PASSWORD')
        self.use_tls = os.environ.get('EMAIL_USE_TLS', 'false').lower() == 'true'  # false por defecto

        if not self.sender_email or not self.sender_password:
            logger.warning("EMAIL_USER o EMAIL_PASSWORD no configurados. El envío fallará.")
        else:
            logger.info("EmailService inicializado con Gmail SMTP SSL")

    def _enviar(self, destinatario: str, nombre: str, asunto: str, html: str) -> bool:
        if not self.sender_email or not self.sender_password:
            logger.error("Faltan credenciales de correo")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = f"Visual Outlet <{self.sender_email}>"
            msg['To'] = destinatario
            msg['Subject'] = asunto
            parte_html = MIMEText(html, 'html')
            msg.attach(parte_html)

            # Conectar con timeout de 5 segundos (para no bloquear al worker)
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=5)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=5)

            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, destinatario, msg.as_string())
            server.quit()

            logger.info(f"✅ Correo enviado a {destinatario}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Autenticación fallida para {destinatario}: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error enviando a {destinatario}: {e}")
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
        return self._enviar(correo, nombre, "Código de verificación — Visual Outlet", html)

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
        return self._enviar(correo, nombre, "Restablecer contraseña — Visual Outlet", html)


email_service = EmailService()

def enviar_codigo_verificacion(correo, nombre, codigo):
    return email_service.enviar_codigo_verificacion(correo, nombre, codigo)

def enviar_codigo_reset(correo, nombre, codigo):
    return email_service.enviar_codigo_reset(correo, nombre, codigo)