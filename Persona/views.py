from django.shortcuts import render, get_object_or_404
from .models import Persona
from Prestamos.models import Prestamo
from django.contrib.auth.decorators import login_required
@login_required
def lista_personas(request):
    personas = Persona.objects.all().order_by('apellidos', 'nombres')
    return render(request, 'persona/lista_personas.html', {'personas': personas})
@login_required
def prestamos_por_persona(request, persona_id):
    persona = get_object_or_404(Persona, pk=persona_id)
    prestamos = persona.prestamos.all().order_by('fecha_inicio')
    return render(
        request,
        'persona/prestamos_por_persona.html',
        {'persona': persona, 'prestamos': prestamos}
    )
