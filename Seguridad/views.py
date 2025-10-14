from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from .services import send_verification_code, verify_code
from Persona.models import Persona
from .forms import NotificacionForm


def _normalize_verify_response(res):
    if isinstance(res, tuple) and len(res) == 2:
        return bool(res[0]), res[1]
    return bool(res), None


def email_step(request):
    if request.method == 'POST':
        email = (request.POST.get('email') or '').strip().lower()
        if not email:
            messages.error(request, 'Ingresa un correo válido.')
            return redirect('seguridad:email')
        try:
            send_verification_code(email)
            request.session['pending_email'] = email
            messages.success(request, f'Enviamos un código a {email}. Revisa tu bandeja.')
            return redirect('seguridad:verify')
        except Exception as e:
            messages.error(request, f'No se pudo enviar el código: {e}')
            return redirect('seguridad:email')
    return render(request, 'seguridad/email_step.html')


def verify_step(request):
    email = request.session.get('pending_email')
    if not email:
        messages.error(request, 'Primero ingresa tu correo.')
        return redirect('seguridad:email')

    if request.method == 'POST':
        code = (request.POST.get('code') or '').strip()
        try:
            ok, err = _normalize_verify_response(verify_code(email, code))
        except Exception:
            ok, err = False, 'No se pudo validar el código. Intenta nuevamente.'
        if not ok:
            messages.error(request, err or 'Código inválido o expirado.')
            return redirect('seguridad:verify')

        user, _ = User.objects.get_or_create(username=email, defaults={'email': email})
        user.backend = 'django.contrib.auth.backends.ModelBackend'
        login(request, user)
        return redirect('seguridad:profile')

    return render(request, 'seguridad/verify_step.html', {'email': email})


def resend_code(request):
    email = request.session.get('pending_email')
    if not email:
        messages.error(request, 'No hay un correo pendiente para reenviar. Ingresa tu correo.')
        return redirect('seguridad:email')
    try:
        send_verification_code(email)
        messages.success(request, f'Código reenviado a {email}.')
    except Exception as e:
        messages.error(request, f'No se pudo reenviar el código: {e}')
    return redirect('seguridad:verify')


@login_required
def profile_step(request):
    """
    Muestra y guarda los datos de la Persona asociada al usuario.
    Precarga campos y valida confirmación de contraseña.
    """
    persona = getattr(request.user, 'persona', None)

    if request.method == 'POST':
        nombres   = (request.POST.get('nombres') or '').strip()
        apellidos = (request.POST.get('apellidos') or '').strip()
        telefono  = (request.POST.get('telefono') or '').strip()
        direccion = (request.POST.get('direccion') or '').strip()
        password  = (request.POST.get('password') or '').strip()
        confirm   = (request.POST.get('confirm_password') or '').strip()

        if not nombres or not apellidos:
            messages.error(request, 'Completa nombres y apellidos.')
            return redirect('seguridad:profile')

        if password or confirm:
            if password != confirm:
                messages.error(request, 'Las contraseñas no coinciden.')
                return redirect('seguridad:profile')

        # Crear/actualizar Persona
        if persona is None:
            persona = Persona.objects.create(
                user=request.user,
                nombres=nombres,
                apellidos=apellidos,
                correo=request.user.email or request.user.username,
                telefono=telefono or None,
                direccion=direccion or None,
            )
        else:
            persona.nombres = nombres
            persona.apellidos = apellidos
            persona.correo = request.user.email or request.user.username
            persona.telefono = telefono or None
            persona.direccion = direccion or None
            persona.save()

        # Cambiar contraseña (opcional)
        if password:
            request.user.set_password(password)
            request.user.save()
            user = authenticate(username=request.user.username, password=password)
            if user:
                login(request, user)

        messages.success(request, 'Perfil actualizado.')
        return redirect('reportes:dashboard')

    # GET: precarga
    ctx = {
        'persona': persona,
        'email_verificado': request.user.email or request.user.username,
    }
    return render(request, 'seguridad/profile_step.html', ctx)


def login_view(request):
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


@login_required
def notification_settings(request):
    persona = getattr(request.user, 'persona', None)
    if not persona:
        messages.error(request, 'Primero completa tu perfil.')
        return redirect('seguridad:profile')

    if request.method == 'POST':
        form = NotificacionForm(request.POST, instance=persona)
        if form.is_valid():
            form.save()
            messages.success(request, 'Preferencias guardadas.')
            return redirect('seguridad:notificaciones')
        messages.error(request, 'Revisa los datos ingresados.')
    else:
        form = NotificacionForm(instance=persona)

    return render(request, 'seguridad/notificaciones.html', {'form': form})
