from datetime import date, timedelta
from django.conf import settings
from django.core.mail import send_mail
from Pagos.models import Pago
from .models import Alerta

def _enviar_correo(destinatario: str, asunto: str, cuerpo: str) -> bool:
    try:
        send_mail(
            subject=asunto,
            message=cuerpo,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[destinatario],
            fail_silently=False,
        )
        return True
    except Exception:
        return False

def generar_y_enviar_alertas(dias_antes: int = 3) -> dict:
    """
    - Encuentra pagos 'Pendiente' cuyo vencimiento sea HOY o dentro de N días.
    - Crea registro Alerta si no existe y envía correo.
    - También envía correo para pagos 'Pendiente' vencidos (fecha_vencimiento < hoy).
    Devuelve resumen {'creadas': n, 'enviadas': n, 'vencidas': n}.
    """
    hoy = date.today()
    hasta = hoy + timedelta(days=dias_antes)

    # Próximos a vencer
    proximos = Pago.objects.select_related('prestamo__persona') \
        .filter(estado='Pendiente', fecha_vencimiento__gte=hoy, fecha_vencimiento__lte=hasta)

    # Ya vencidos (aún Pendiente)
    vencidos = Pago.objects.select_related('prestamo__persona') \
        .filter(estado='Pendiente', fecha_vencimiento__lt=hoy)

    creadas = enviadas = vencidas_count = 0

    # Helper local
    def procesar_pago(pago, es_vencido=False):
        nonlocal creadas, enviadas, vencidas_count
        persona = pago.prestamo.persona
        if not persona.correo:
            return
        # Evitar duplicados: una alerta por pago y fecha_alerta (hoy)
        alerta, creada = Alerta.objects.get_or_create(
            pago=pago, fecha_alerta=hoy,
            defaults={
                'mensaje': f"Recordatorio de pago de la cuota {pago.numero_cuota} "
                           f"del préstamo en {pago.prestamo.banco}. "
                           f"Vence el {pago.fecha_vencimiento}. Monto: {pago.monto}",
                'estado': 'Pendiente'
            }
        )
        if creada:
            creadas += 1
        # Enviar correo si aún está Pendiente
        asunto = ("Pago VENCIDO" if es_vencido else "Recordatorio de pago próximo")
        cuerpo = (f"Hola {persona.nombres},\n\n"
                  f"{'Tu pago está VENCIDO' if es_vencido else 'Tienes un pago próximo'}.\n\n"
                  f"Banco: {pago.prestamo.banco}\n"
                  f"Cuota: {pago.numero_cuota}\n"
                  f"Vencimiento: {pago.fecha_vencimiento}\n"
                  f"Monto: {pago.monto}\n\n"
                  f"Por favor realiza el pago para evitar cargos adicionales.\n\n"
                  f"Saludos.")
        ok = _enviar_correo(persona.correo, asunto, cuerpo)
        if ok:
            alerta.estado = 'Enviada'
            alerta.save(update_fields=['estado'])
            enviadas += 1
        if es_vencido:
            vencidas_count += 1

    for p in proximos:
        procesar_pago(p, es_vencido=False)
    for p in vencidos:
        procesar_pago(p, es_vencido=True)

    return {'creadas': creadas, 'enviadas': enviadas, 'vencidas': vencidas_count}
