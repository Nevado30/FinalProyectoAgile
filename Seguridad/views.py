from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required  # opcional si luego usas auth
from .services import send_verification_code, verify_code, MIN_RETRY_SECONDS
from Persona.models import Persona

SESSION_PENDING_EMAIL = 'pending_email'
SESSION_VERIFIED_EMAIL = 'verified_email'

@require_http_methods(["GET", "POST"])
def email_step(request):
    if request.method == "POST":
        email = (request.POST.get('email') or "").strip().lower()
        if not email:
            messages.error(request, "Ingresa un correo válido.")
            return redirect('seguridad:email')

        ev = send_verification_code(email)
        request.session[SESSION_PENDING_EMAIL] = email

        # anti-spam feedback
        messages.success(request, f"Te enviamos un código a {email}. Revisa tu bandeja (o spam).")
        return redirect('seguridad:verify')

    return render(request, 'seguridad/email_step.html')

@require_http_methods(["GET", "POST"])
def verify_step(request):
    email = request.session.get(SESSION_PENDING_EMAIL)
    if not email:
        messages.info(request, "Primero ingresa tu correo.")
        return redirect('seguridad:email')

    if request.method == "POST":
        code = request.POST.get('code', '').strip()
        if verify_code(email, code):
            request.session[SESSION_VERIFIED_EMAIL] = email
            request.session.pop(SESSION_PENDING_EMAIL, None)
            messages.success(request, "Correo verificado correctamente.")
            return redirect('seguridad:profile')
        messages.error(request, "Código inválido o expirado. Inténtalo de nuevo.")

    return render(request, 'seguridad/verify_step.html', {'email': email})

def resend_code(request):
    email = request.session.get(SESSION_PENDING_EMAIL)
    if not email:
        return redirect('seguridad:email')
    ev = send_verification_code(email)
    messages.info(request, f"Reenviamos el código a {email}. (Puede tardar unos segundos)")
    return redirect('seguridad:verify')

def require_verified(func):
    def _wrap(request, *args, **kwargs):
        if not request.session.get(SESSION_VERIFIED_EMAIL):
            messages.info(request, "Verifica tu correo para continuar.")
            return redirect('seguridad:email')
        return func(request, *args, **kwargs)
    return _wrap

@require_verified
@require_http_methods(["GET", "POST"])
def profile_step(request):
    email = request.session[SESSION_VERIFIED_EMAIL]
    persona = Persona.objects.filter(correo=email).first()

    if request.method == "POST":
        nombres = request.POST.get('nombres', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        direccion = request.POST.get('direccion', '').strip()

        if not (nombres and apellidos):
            messages.error(request, "Nombres y apellidos son obligatorios.")
            return redirect('seguridad:profile')

        if persona:
            persona.nombres = nombres
            persona.apellidos = apellidos
            persona.telefono = telefono or None
            persona.direccion = direccion or None
            persona.save()
        else:
            persona = Persona.objects.create(
                correo=email, nombres=nombres, apellidos=apellidos,
                telefono=telefono or None, direccion=direccion or None
            )

        messages.success(request, "Datos guardados. ¡Bienvenido!")
        # aquí puedes guardar persona.id en sesión si luego usas “sesión por correo”
        request.session['persona_id'] = persona.id_persona
        return redirect('/reportes/')  # o a donde quieras

    # GET: cargar valores existentes si hay
    ctx = {
        'email': email,
        'persona': persona,
    }
    return render(request, 'seguridad/profile_step.html', ctx)
