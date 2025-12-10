from datetime import date, timedelta
from django.conf import settings
from django.core.mail import send_mail

from Persona.models import Persona
from Pagos.models import Pago
from Moneda.services import convertir_monto
from .sms import send_sms
from .models import Alerta
# ^ si ya lo tenías importado, deja solo una vez


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


def _crear_alerta(pago, fecha_alerta, mensaje):
    """
    Helper opcional para registrar la alerta en la tabla Alertas.
    Si ya lo tenías definido, deja tu versión; este es un ejemplo.
    """
    return Alerta.objects.create(
        pago=pago,
        fecha_alerta=fecha_alerta,
        mensaje=mensaje,
        estado='Pendiente',
    )


# ============================================================
#  FUNCIÓN QUE YA TENÍAS: proceso masivo (posible job diario)
# ============================================================
def generar_y_enviar_alertas(dias_antes: int = None, solo_hoy: bool = False, modo_prueba: bool = False):
    """
    Recorre todas las personas y:
      - busca pagos Pendientes
      - genera alertas para:
          * cuotas próximas según noti_dias
          * cuotas vencidas (fecha_vencimiento < hoy)
      - envía por email / SMS según flags noti_email / noti_sms
    """
    hoy = date.today()
    creadas = 0
    enviadas = 0

    for persona in Persona.objects.all():
        base = (getattr(persona, 'moneda_preferida', None) or 'PEN').upper()

        if solo_hoy:
            dias_list = [0]
        else:
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

        # -------- EMAIL --------
        if getattr(persona, 'noti_email', False) and persona.correo:
            for p in proximos:
                mensaje = cuerpo_email(p)
                _crear_alerta(p, hoy, mensaje)
                if not modo_prueba:
                    if _send_email(persona.correo, f"[Recordatorio] Cuota {p.numero_cuota}", mensaje):
                        enviadas += 1
                else:
                    print(f"[SIMULADO EMAIL] a {persona.correo}: {mensaje}")

            for p in vencidos:
                mensaje = cuerpo_email(p)
                _crear_alerta(p, hoy, mensaje)
                if not modo_prueba:
                    if _send_email(persona.correo, f"[Vencido] Cuota {p.numero_cuota}", mensaje):
                        enviadas += 1
                else:
                    print(f"[SIMULADO EMAIL VENCIDO] a {persona.correo}: {mensaje}")

        # -------- SMS (VONAGE) --------
        if getattr(persona, 'noti_sms', False) and getattr(persona, 'telefono', None):
            for p in proximos:
                texto = cuerpo_sms(p)
                _crear_alerta(p, hoy, texto)

                if modo_prueba or not getattr(settings, 'SMS_ENABLED', False):
                    print(f"[SIMULADO SMS] a {persona.telefono}: {texto}")
                else:
                    ok, _ = send_sms(persona.telefono, texto)
                    if ok:
                        enviadas += 1

            for p in vencidos:
                texto = "[Vencido] " + cuerpo_sms(p)
                _crear_alerta(p, hoy, texto)

                if modo_prueba or not getattr(settings, 'SMS_ENABLED', False):
                    print(f"[SIMULADO SMS VENCIDO] a {persona.telefono}: {texto}")
                else:
                    ok, _ = send_sms(persona.telefono, texto)
                    if ok:
                        enviadas += 1

        creadas += proximos.count() + vencidos.count()

    return {'creadas': creadas, 'enviadas': enviadas}


# ============================================================
#  NUEVO: ALERTA INMEDIATA AL CREAR / EDITAR UN PAGO
# ============================================================
def enviar_alerta_inmediata_por_pago(pago):
    """
    Se usa justo después de crear un Pago.
    Manda alerta si:
      - el pago está Pendiente
      - Y vence HOY o ya está vencido (fecha_vencimiento <= hoy)
    Respeta las preferencias de la Persona (noti_email, noti_sms)
    y el flag global SMS_ENABLED.
    """
    hoy = date.today()

    if getattr(pago, "estado", "") != "Pendiente":
        return False, "Pago no pendiente"

    if pago.fecha_vencimiento > hoy:
        return False, "Todavía no corresponde enviar alerta inmediata"

    persona = pago.prestamo.persona
    base = (getattr(persona, "moneda_preferida", None) or "PEN").upper()
    origen = pago.prestamo.moneda_prestamo or "PEN"
    monto = convertir_monto(pago.monto, origen, base, pago.fecha_vencimiento)

    asunto = f"Recordatorio de cuota {pago.numero_cuota}"
    cuerpo = (
        f"Hola {persona.nombres},\n\n"
        f"Cuota {pago.numero_cuota} del préstamo en {pago.prestamo.banco}.\n"
        f"Vence: {pago.fecha_vencimiento}.\n"
        f"Monto a pagar (en {base}): {monto}.\n\n"
        "Ingresa a la app para registrar el pago."
    )

    sms_text = (
        f"Cuota {pago.numero_cuota} {pago.prestamo.banco} "
        f"vence {pago.fecha_vencimiento} - {monto} {base}"
    )

    enviados = 0

    # Email inmediato
    if getattr(persona, "noti_email", False) and persona.correo:
        _crear_alerta(pago, hoy, cuerpo)
        if _send_email(persona.correo, asunto, cuerpo):
            enviados += 1

    # SMS inmediato
    if getattr(persona, "noti_sms", False) and getattr(persona, "telefono", None):
        _crear_alerta(pago, hoy, sms_text)

        if getattr(settings, "SMS_ENABLED", False):
            ok, _ = send_sms(persona.telefono, sms_text)
            if ok:
                enviados += 1
        else:
            # modo “seguro” por si olvidas apagar SMS_ENABLED en pruebas
            print(f"[SIMULADO SMS INMEDIATO] a {persona.telefono}: {sms_text}")

    if enviados == 0:
        return False, "Sin canales activos o SMS deshabilitado"

    return True, f"Notificaciones inmediatas enviadas: {enviados}"
