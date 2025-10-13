from django.shortcuts import render, get_object_or_404
from .models import Prestamo
from Pagos.models import Pago  
from django.contrib.auth.decorators import login_required

@login_required
def lista_prestamos(request):
    prestamos = Prestamo.objects.select_related('persona').order_by('persona__apellidos', 'fecha_inicio')
    return render(request, 'prestamos/lista_prestamos.html', {'prestamos': prestamos})
@login_required
def pagos_por_prestamo(request, prestamo_id):
    prestamo = get_object_or_404(Prestamo, pk=prestamo_id)
    pagos = prestamo.pagos.all().order_by('numero_cuota')
    return render(
        request,
        'prestamos/pagos_por_prestamo.html',
        {'prestamo': prestamo, 'pagos': pagos}
    )
