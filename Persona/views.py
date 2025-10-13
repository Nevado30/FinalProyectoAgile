from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import Persona
from Prestamos.models import Prestamo

@login_required
def lista_personas(request):
    # Cada usuario ve SOLO su propia Persona
    personas = Persona.objects.filter(user=request.user)
    return render(request, 'persona/lista_personas.html', {'personas': personas})

@login_required
def prestamos_por_persona(request, persona_id: int):
    persona = get_object_or_404(Persona, pk=persona_id, user=request.user)
    prestamos = Prestamo.objects.filter(persona=persona)
    return render(request, 'persona/prestamos_por_persona.html', {
        'persona': persona,
        'prestamos': prestamos,
    })
