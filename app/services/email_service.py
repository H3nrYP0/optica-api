import os
import re
import logging
import resend

# Configuración básica para que los logs se muestren en consola
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.api_key = os.environ.get('RESEND_API_KEY')
        self.mode = os.environ.get('RESEND_MODE', 'REAL')  # TEST_EVENTS o REAL
        self.sender = os.environ.get('RESEND_FROM_EMAIL', 'onboarding@resend.dev')
        
        if self.api_key:
            resend.api_key = self.api_key
            logger.info(f"Resend inicializado en modo {self.mode}")
        else:
            logger.warning("RESEND_API_KEY no configurada")

    def _esta_configurado(self) -> bool:
        return bool(self.api_key)

    def _sanitize_ascii(self, text: str) -> str:
        """Elimina caracteres no ASCII y reemplaza espacios por guiones bajos."""
        # Elimina cualquier carácter que no sea letra (A-Za-z), número, espacio o guion bajo
        clean = re.sub(r'[^A-Za-z0-9\s_]', '', text)
        # Reemplaza espacios por guiones bajos
        return clean.replace(' ', '_')

    def _get_test_destination(self, asunto: str, nombre: str) -> str:
        """Elige la dirección mágica según el tipo de correo, con nombre sanitizado."""
        asunto_lower = asunto.lower()
        nombre_ascii = self._sanitize_ascii(nombre)
        if "verificación" in asunto_lower:
            return f"delivered+verificacion_{nombre_ascii}@resend.dev"
        elif "contraseña" in asunto_lower or "reset" in asunto_lower:
            return "delivered+password_reset@resend.dev"
        else:
            return "delivered@resend.dev"

    def _enviar(self, destinatario_email: str, destinatario_nombre: str,
                asunto: str, html: str) -> bool:
        if not self._esta_configurado():
            logger.error("Resend no configurado")
            return False

        try:
            # Si estamos en modo pruebas, usamos dirección mágica
            if self.mode == "TEST_EVENTS":
                destino_real = self._get_test_destination(asunto, destinatario_nombre)
                # Añadimos información del destinatario original en el HTML para depuración
                html_con_nota = f"""
                <p><strong>[MODO PRUEBAS]</strong> Este correo fue simulado para: 
                {destinatario_nombre} &lt;{destinatario_email}&gt;</p>
                <hr>
                {html}
                """
                params = {
                    "from": self.sender,
                    "to": [destino_real],
                    "subject": f"[SIM] {asunto}",
                    "html": html_con_nota,
                }
                logger.info(f"Modo pruebas: enviando a dirección mágica {destino_real} (original: {destinatario_email})")
            else:
                # Modo real (requiere dominio verificado y remitente válido)
                params = {
                    "from": f"Visual Outlet <{self.sender}>",
                    "to": [destinatario_email],
                    "subject": asunto,
                    "html": html,
                }

            resp = resend.Emails.send(params)
            logger.info(f"✅ Email {'simulado ' if self.mode == 'TEST_EVENTS' else ''}enviado. ID: {resp.get('id')}")
            return True

        except Exception as e:
            logger.error(f"❌ Error enviando a {destinatario_email}: {e}")
            return False

    def enviar_codigo_verificacion(self, correo: str, nombre: str, codigo: str) -> bool:
        # Codigo se impreme en consola para facilitar las pruebas, borrar en producción. 
        # En modo REAL, el código se envía al correo del usuario. En modo TEST_EVENTS, se envía a la dirección mágica y se muestra en el HTML para verificación. 
        # Lo mismo para el resto de funciones de envío de correo.
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


# Instancia única (compatible con imports actuales)
email_service = EmailService()

def enviar_codigo_verificacion(correo, nombre, codigo):
    return email_service.enviar_codigo_verificacion(correo, nombre, codigo)

def enviar_codigo_reset(correo, nombre, codigo):
    return email_service.enviar_codigo_reset(correo, nombre, codigo)