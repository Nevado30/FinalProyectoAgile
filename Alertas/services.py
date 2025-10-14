from datetime import date, timedelta
from django.conf import settings
from django.core.mail import send_mail

from Persona.models import Persona
from Pagos.models import Pago
from Moneda.services import convertir_monto

from .sms import send_sms


def _parse_days(raw: str, fallback=3):
    """Convierte '7,3,1,0' -> [7,3,1,0] (únicos, >=0, orden desc)."""
    try:
        parts = [s.strip() for s in (raw or '').split(',')]
        vals = [int(v) for v in parts if v != '']
        vals = sorted(set(v for v in vals if v >= 0), reverse=True)
        return vals or [fallback]
    except Exception:
        return [fallback]


def _send_email(to, subject, body) -> bool:
    if not to:
        return False
    send_mail(
        subject=subject,
        message=body,
        from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', None) or 'no-reply@example.com',
        recipient_list=[to],
        fail_silently=False,
    )
    return True


def generar_y_enviar_alertas(dias_antes: int = None):
    hoy = date.today()
    creadas = 0
    enviadas = 0

    for persona in Persona.objects.all():
        base = (getattr(persona, 'moneda_preferida', None) or 'PEN').upper()
        dias_list = _parse_days(
            getattr(persona, 'noti_dias', ''),
            fallback=(dias_antes if dias_antes is not None else 3),
        )
        fechas_obj = [hoy + timedelta(days=d) for d in dias_list]

        qs = Pago.objects.filter(prestamo__persona=persona, estado='Pendiente')
        proximos = qs.filter(fecha_vencimiento__in=fechas_obj)
        vencidos = qs.filter(fecha_vencimiento__lt=hoy)

        def cuerpo_email(pago):
            origen = pago.prestamo.moneda_prestamo or 'PEN'
            monto = convertir_monto(pago.monto, origen, base, pago.fecha_vencimiento)
            return (
                f"Hola {persona.nombres},\n\n"
                f"Cuota {pago.numero_cuota} del préstamo en {pago.prestamo.banco}.\n"
                f"Vence: {pago.fecha_vencimiento}.\n"
                f"Monto a pagar (en {base}): {monto}.\n\n"
                "Ingresa a la app para marcar el pago."
            )

        def cuerpo_sms(pago):
            origen = pago.prestamo.moneda_prestamo or 'PEN'
            monto = convertir_monto(pago.monto, origen, base, pago.fecha_vencimiento)
            return (
                f"Cuota {pago.numero_cuota} {pago.prestamo.banco} "
                f"vence {pago.fecha_vencimiento}. "
                f"Importe: {monto} {base}"
            )

        # --- EMAIL ---
        if getattr(persona, 'noti_email', False):
            for p in proximos:
                if _send_email(persona.correo, f"[Recordatorio] Cuota {p.numero_cuota}", cuerpo_email(p)):
                    enviadas += 1
            for p in vencidos:
                if _send_email(persona.correo, f"[Vencido] Cuota {p.numero_cuota}", cuerpo_email(p)):
                    enviadas += 1

        # --- SMS ---
        if getattr(persona, 'noti_sms', False) and getattr(persona, 'telefono', None):
            for p in proximos:
                ok, _ = send_sms(persona.telefono, cuerpo_sms(p))
                if ok:
                    enviadas += 1
            for p in vencidos:
                ok, _ = send_sms(persona.telefono, "[Vencido] " + cuerpo_sms(p))
                if ok:
                    enviadas += 1

        # Total de alertas generadas (independiente del canal)
        creadas += proximos.count() + vencidos.count()

    return {'creadas': creadas, 'enviadas': enviadas}
