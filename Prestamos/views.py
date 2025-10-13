from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from .models import Prestamo
from .forms import PrestamoForm
from Persona.models import Persona
from Pagos.models import Pago

@login_required
def lista_prestamos(request):
    prestamos = (
        Prestamo.objects
        .filter(persona__user=request.user)
        .select_related('persona')
        .order_by('id_prestamo')  # PK real
    )
    return render(request, 'prestamos/lista_prestamos.html', {'prestamos': prestamos})

@login_required
def pagos_por_prestamo(request, prestamo_id: int):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_id, persona__user=request.user)
    pagos = Pago.objects.filter(prestamo=prestamo).order_by('numero_cuota')
    return render(request, 'prestamos/pagos_por_prestamo.html', {'prestamo': prestamo, 'pagos': pagos})

@login_required
def crear_prestamo(request):
    persona = getattr(request.user, 'persona', None)
    if persona is None:
        messages.error(request, 'Primero completa tu perfil para vincular tu cuenta a una Persona.')
        return redirect('seguridad:profile_step')

    if request.method == 'POST':
        form = PrestamoForm(request.POST)
        if form.is_valid():
            prestamo = form.save(commit=False)
            prestamo.persona = persona
            prestamo.save()  # dispara la signal que crea las cuotas
            messages.success(request, 'Préstamo creado y cuotas generadas automáticamente.')
            return redirect('prestamos:lista')
        messages.error(request, 'Revisa los campos del formulario.')
    else:
        form = PrestamoForm()

    return render(request, 'prestamos/nuevo.html', {'form': form})
