from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Prestamo
from .forms import PrestamoForm
from Pagos.models import Pago
from .signals import generar_cuotas


@login_required
def lista_prestamos(request):
    prestamos = (
        Prestamo.objects
        .filter(persona__user=request.user)
        .select_related('persona')
        .order_by('id_prestamo')
    )
    return render(request, 'prestamos/lista_prestamos.html', {'prestamos': prestamos})


@login_required
def pagos_por_prestamo(request, prestamo_id: int):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_id, persona__user=request.user)
    pagos = Pago.objects.filter(prestamo=prestamo).order_by('numero_cuota')
    return render(request, 'prestamos/pagos_por_prestamo.html', {
        'prestamo': prestamo,
        'pagos': pagos,
    })


@login_required
def crear_prestamo(request):
    persona = getattr(request.user, 'persona', None)
    if persona is None:
        messages.error(request, 'Primero completa tu perfil para vincular tu cuenta a una Persona.')
        return redirect('seguridad:profile')

    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.persona = persona
            prestamo.save()  # dispara generación automática
            messages.success(request, 'Préstamo creado y cuotas generadas automáticamente.')
            return redirect('prestamos:lista')
        messages.error(request, 'Revisa los campos del formulario.')
    else:
        form = PrestamoForm()

    return render(request, 'prestamos/nuevo.html', {'form': form})


@login_required
def editar_prestamo(request, prestamo_id: int):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_id, persona__user=request.user)
    tiene_pagados = Pago.objects.filter(prestamo=prestamo, estado='Pagado').exists()

    if request.method == 'POST':
        form = PrestamoForm(request.POST, instance=prestamo)
        if form.is_valid():
            if tiene_pagados:
                # Con pagos realizados: solo permitimos editar campos no estructurales
                prestamo.banco = form.cleaned_data.get('banco')
                prestamo.descripcion = form.cleaned_data.get('descripcion')
                prestamo.tasa_interes = form.cleaned_data.get('tasa_interes')  # opcional visual
                prestamo.save(update_fields=['banco', 'descripcion', 'tasa_interes'])
                messages.info(request, 'Se actualizaron los datos del préstamo. No se recalcularon cuotas porque ya hay pagos registrados.')
            else:
                # Sin pagos: actualiza y **recalcula** el cronograma completo
                form.save()
                Pago.objects.filter(prestamo=prestamo).delete()
                generar_cuotas(prestamo)
                messages.success(request, 'Préstamo actualizado y cuotas recalculadas.')
            return redirect('prestamos:lista')
        messages.error(request, 'Revisa los campos del formulario.')
    else:
        form = PrestamoForm(instance=prestamo)

    return render(request, 'prestamos/editar.html', {
        'form': form,
        'prestamo': prestamo,
        'tiene_pagados': tiene_pagados,
    })


@login_required
def eliminar_prestamo(request, prestamo_id: int):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_id, persona__user=request.user)
    tiene_pagados = Pago.objects.filter(prestamo=prestamo, estado='Pagado').exists()

    if request.method == 'POST':
        if tiene_pagados:
            messages.error(request, 'No puedes eliminar un préstamo que ya tiene pagos registrados. (Evita perder historial).')
            return redirect('prestamos:lista')
        prestamo.delete()
        messages.success(request, 'Préstamo eliminado.')
        return redirect('prestamos:lista')

    return render(request, 'prestamos/confirmar_eliminar.html', {
        'prestamo': prestamo,
        'tiene_pagados': tiene_pagados,
    })
