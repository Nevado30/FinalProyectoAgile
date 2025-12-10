# Alertas/sms.py
from django.conf import settings

try:
    # SDK moderno de Vonage
    from vonage import Vonage, Auth
    from vonage_sms import SmsMessage
    HAS_VONAGE = True
except ImportError:
    HAS_VONAGE = False


def _to_e164(numero: str, default_cc='+51'):
    """
    Normaliza un número celular al formato E.164 (ej: +51904929929)
    Usamos Perú (+51) como código por defecto.
    """
    n = str(numero or '').strip().replace(' ', '').replace('-', '')
    if not n:
        return None

    # Si ya viene con +, lo dejamos
    if n.startswith('+'):
        return n

    # Si viene con 00 (ej: 0051...), quitamos los dos ceros
    if n.startswith('00'):
        return '+' + n[2:]

    # Celular típico de Perú: 9 dígitos empezando en 9
    if len(n) == 9 and n[0] == '9':
        return default_cc + n

    # Fallback: pegamos el código de país por defecto
    return default_cc + n


def send_sms(numero: str, mensaje: str):
    """
    Envía un SMS usando Vonage.
    Retorna: (ok: bool, detalle: str)
    """
    # 1. Config apagada
    if not getattr(settings, 'VONAGE_SMS_ENABLED', False):
        return False, 'SMS deshabilitado por configuración'

    # 2. SDK no instalado
    if not HAS_VONAGE:
        return False, 'SDK de Vonage no está instalado (pip install vonage vonage-sms)'

    api_key = getattr(settings, 'VONAGE_API_KEY', None)
    api_secret = getattr(settings, 'VONAGE_API_SECRET', None)
    from_ = getattr(settings, 'VONAGE_FROM_NUMBER', None)

    # 3. Credenciales incompletas
    if not (api_key and api_secret and from_):
        return False, 'Credenciales Vonage incompletas (revisa .env y settings.py)'

    # 4. Normalizar número
    to = _to_e164(numero)
    if not to:
        return False, 'Número destino inválido'

    try:
        # 5. Crear cliente Vonage
        auth = Auth(api_key=api_key, api_secret=api_secret)
        client = Vonage(auth=auth)

        # 6. Crear mensaje SMS
        message = SmsMessage(
            to=to,
            from_=from_,
            text=mensaje,
        )

        # 7. Enviar mensaje
        response = client.sms.send(message)
        data = response.model_dump(exclude_unset=True)
        print(data)

        return True, 'SMS enviado correctamente'

    except Exception as e:
        return False, str(e)
