from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required 
from .services import send_verification_code, verify_code, MIN_RETRY_SECONDS
from Persona.models import Persona
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout

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
    persona = Persona.objects.filter(correo=email).select_related(
        *(['user'] if hasattr(Persona, 'user') else [])
    ).first()

    if request.method == "POST":
        nombres   = (request.POST.get('nombres') or '').strip()
        apellidos = (request.POST.get('apellidos') or '').strip()
        telefono  = (request.POST.get('telefono') or '').strip()
        direccion = (request.POST.get('direccion') or '').strip()
        password  = (request.POST.get('password') or '').strip()
        confirm   = (request.POST.get('confirm') or '').strip()

        if not (nombres and apellidos):
            messages.error(request, "Nombres y apellidos son obligatorios.")
            return redirect('seguridad:profile')

        # Crear/actualizar Persona
        if persona:
            persona.nombres   = nombres
            persona.apellidos = apellidos
            persona.telefono  = telefono or None
            persona.direccion = direccion or None
            persona.save()
        else:
            persona = Persona.objects.create(
                correo=email,
                nombres=nombres,
                apellidos=apellidos,
                telefono=telefono or None,
                direccion=direccion or None
            )

        user, created = User.objects.get_or_create(
            username=email, defaults={'email': email}
        )
        user.email = email

        if created or password:
            if not password:
                messages.error(request, "Debes definir una contraseña para tu cuenta.")
                return redirect('seguridad:profile')
            if password != confirm:
                messages.error(request, "Las contraseñas no coinciden.")
                return redirect('seguridad:profile')
            user.set_password(password)

        user.is_active = True
        user.save()

        if hasattr(persona, 'user'):
            if not getattr(persona, 'user_id', None) or persona.user_id != user.id:
                persona.user = user
                persona.save(update_fields=['user'])

        from django.contrib.auth import login
        login(request, user)

        request.session['persona_id'] = getattr(persona, 'id_persona', None)
        messages.success(request, "Cuenta lista e inicio de sesión correcto. ¡Bienvenido!")
        return redirect('/reportes/')

    # GET
    ctx = {
        'email': email,
        'persona': persona,
        'tiene_user': bool(getattr(persona, 'user', None)) if persona and hasattr(persona, 'user') else False,
    }
    return render(request, 'seguridad/profile_step.html', ctx)

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.method == "POST":
        email = (request.POST.get('email') or "").lower().strip()
        password = request.POST.get('password') or ""
        remember = request.POST.get('remember') == 'on'

        # buscamos por username=email
        user = authenticate(request, username=email, password=password)
        if user:
            login(request, user)
            # “Recuérdame”: sesión persistente por 2 semanas; si no, expira al cerrar navegador
            request.session.set_expiry(1209600 if remember else 0)
            return redirect('/reportes/')
        messages.error(request, "Credenciales incorrectas.")
    return render(request, 'seguridad/login.html')

def logout_view(request):
    logout(request)
    return redirect('seguridad:login')
