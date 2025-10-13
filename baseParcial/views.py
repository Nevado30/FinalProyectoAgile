from django.shortcuts import redirect
from django.urls import reverse

def home_redirect(request):
    # Fuerza mostrar la pantalla de login, incluso si hay sesión iniciada
    login_url = reverse('seguridad:login')
    return redirect(f'{login_url}?force=1')
