from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .services import send_verification_code, verify_code
from Persona.models import Persona


def _normalize_verify_response(res):
    """
    Acepta respuesta de verify_code como bool o como (ok, err).
    Retorna (ok: bool, err: str|None)
    """
    if isinstance(res, tuple) and len(res) == 2:
        return bool(res[0]), res[1]
    return bool(res), None


def email_step(request):
    """
    Paso 1: pedir correo y enviar código (con anti-spam en services).
    """
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        if not email:
            messages.error(request, 'Ingresa un correo válido.')
            return redirect('seguridad:email_step')
        try:
            send_verification_code(email)
            request.session['pending_email'] = email
            messages.success(request, f'Enviamos un código a {email}. Revisa tu bandeja.')
            return redirect('seguridad:verify_step')
        except Exception as e:
            messages.error(request, f'No se pudo enviar el código: {e}')
            return redirect('seguridad:email_step')

    return render(request, 'seguridad/email_step.html')


def verify_step(request):
    """
    Paso 2: validar código. Si ok, loguea/crea usuario y pasa a perfil.
    """
    email = request.session.get('pending_email')
    if not email:
        messages.error(request, 'Primero ingresa tu correo.')
        return redirect('seguridad:email_step')

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        try:
            ok, err = _normalize_verify_response(verify_code(email, code))
        except Exception:
            ok, err = False, 'No se pudo validar el código. Intenta nuevamente.'

        if not ok:
            messages.error(request, err or 'Código inválido o expirado.')
            return redirect('seguridad:verify_step')

        user, _ = User.objects.get_or_create(username=email, defaults={'email': email})
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('seguridad:profile_step')

    return render(request, 'seguridad/verify_step.html', {'email': email})


def resend_code(request):
    """
    Reenviar el código al correo guardado en sesión.
    """
    email = request.session.get('pending_email')
    if not email:
        messages.error(request, 'No hay un correo pendiente para reenviar. Ingresa tu correo.')
        return redirect('seguridad:email_step')

    try:
        send_verification_code(email)
        messages.success(request, f'Código reenviado a {email}.')
    except Exception as e:
        messages.error(request, f'No se pudo reenviar el código: {e}')
    return redirect('seguridad:verify_step')


@login_required
def profile_step(request):
    """
    Paso 3: completar/actualizar Persona y permitir setear contraseña.
    """
    if request.method == 'POST':
        nombres = (request.POST.get('nombres') or '').strip()
        apellidos = (request.POST.get('apellidos') or '').strip()
        telefono = (request.POST.get('telefono') or '').strip()
        direccion = (request.POST.get('direccion') or '').strip()
        password = (request.POST.get('password') or '').strip()

        if not nombres or not apellidos:
            messages.error(request, 'Completa nombres y apellidos.')
            return redirect('seguridad:profile_step')

        persona, _ = Persona.objects.get_or_create(
            user=request.user,
            defaults={
                'nombres': nombres,
                'apellidos': apellidos,
                'correo': request.user.email or request.user.username,
                'telefono': telefono or None,
                'direccion': direccion or None,
            },
        )
        # Actualizar si ya existe
        persona.nombres = nombres
        persona.apellidos = apellidos
        persona.correo = request.user.email or request.user.username
        persona.telefono = telefono or None
        persona.direccion = direccion or None
        persona.save()

        if password:
            request.user.set_password(password)
            request.user.save()
            user = authenticate(username=request.user.username, password=password)
            if user:
                login(request, user)

        messages.success(request, 'Perfil completado.')
        return redirect('reportes:dashboard')

    persona = getattr(request.user, 'persona', None)
    initial = {}
    if persona:
        initial = {
            'nombres': persona.nombres,
            'apellidos': persona.apellidos,
            'telefono': persona.telefono or '',
            'direccion': persona.direccion or '',
        }
    return render(request, 'seguridad/profile_step.html', {'initial': initial})


def login_view(request):
    """
    Login clásico. Si ya está autenticado, redirige a reportes (a menos que ?force=1).
    """
    force = request.GET.get('force') == '1'
    if request.user.is_authenticated and not force:
        return redirect('reportes:dashboard')

    if request.method == 'POST':
        login_id = (request.POST.get('username') or request.POST.get('email') or '').strip().lower()
        password = (request.POST.get('password') or '').strip()

        user = authenticate(username=login_id, password=password)
        if not user:
            try:
                u = User.objects.get(email__iexact=login_id)
                user = authenticate(username=u.username, password=password)
            except User.DoesNotExist:
                user = None

        if user:
            login(request, user)
            next_url = request.GET.get('next') or 'reportes:dashboard'
            return redirect(next_url)

        messages.error(request, 'Credenciales inválidas.')
        return redirect('seguridad:login')

    return render(request, 'seguridad/login.html')


@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('seguridad:login')
