from twilio.rest import Client
from django.conf import settings

def _to_e164(numero: str, default_cc='+51'):
    n = str(numero or '').strip().replace(' ', '').replace('-', '')
    if not n:
        return None
    if n.startswith('+'):
        return n
    if n.startswith('00'):  # 0051...
        return '+' + n[2:]
    # Perú móvil típico: 9 dígitos comenzando en 9
    if len(n) == 9 and n[0] == '9':
        return default_cc + n
    # fallback: prepende CC por defecto
    return default_cc + n

def send_sms(numero: str, mensaje: str):
    """Retorna (ok, detalle). Maneja Trial y credenciales faltantes."""
    if not getattr(settings, 'TWILIO_SMS_ENABLED', False):
        return False, 'SMS deshabilitado por configuración'

    sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
    tok = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
    from_ = getattr(settings, 'TWILIO_FROM_NUMBER', None)
    if not (sid and tok and from_):
        return False, 'Credenciales Twilio incompletas'

    to = _to_e164(numero)
    if not to:
        return False, 'Número destino inválido'

    try:
        client = Client(sid, tok)
        msg = client.messages.create(from_=from_, to=to, body=mensaje)
        return True, msg.sid
    except Exception as e:
        # Ej. en Trial: “To number not verified…”
        return False, str(e)
