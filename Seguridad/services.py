import random
from datetime import timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import EmailVerification

MIN_RETRY_SECONDS = 60       # anticiclado de reenvío
CODE_TTL_MINUTES  = 10       # vence en 10 min
MAX_ATTEMPTS      = 5

def _gen_code() -> str:
    return f"{random.randint(1000, 9999)}"  # 4 dígitos

def send_verification_code(email: str) -> EmailVerification:
    now = timezone.now()
    # anti-spam: si se envió hace menos de 60s, no reenviar aún
    last = EmailVerification.objects.filter(email=email).order_by('-created_at').first()
    if last and (now - last.last_sent_at).total_seconds() < MIN_RETRY_SECONDS:
        return last  # devolvemos el último (mensaje en la vista)

    code = _gen_code()
    ev = EmailVerification.objects.create(
        email=email,
        code=code,
        expires_at=now + timedelta(minutes=CODE_TTL_MINUTES),
        last_sent_at=now,
    )

    subject = "Código de verificación"
    body = (
        f"Hola,\n\n"
        f"Tu código de verificación es: {code}\n"
        f"Vence en {CODE_TTL_MINUTES} minutos.\n\n"
        f"Si no solicitaste este código, ignora este correo."
    )
    send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return ev

def verify_code(email: str, code: str) -> bool:
    ev = EmailVerification.objects.filter(email=email, used=False).order_by('-created_at').first()
    if not ev:
        return False
    if ev.is_expired:
        return False
    if ev.attempts >= MAX_ATTEMPTS:
        return False
    # comparar
    if ev.code == code.strip():
        ev.used = True
        ev.save(update_fields=['used'])
        return True
    # intento fallido
    ev.attempts += 1
    ev.save(update_fields=['attempts'])
    return False
