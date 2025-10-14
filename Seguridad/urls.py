from django.urls import path
from . import views

app_name = 'seguridad'

urlpatterns = [
    path('email/',     views.email_step,          name='email'),
    path('verificar/', views.verify_step,         name='verify'),
    path('reenviar/',  views.resend_code,         name='resend'),
    path('perfil/',    views.profile_step,        name='profile'),
    path('notificaciones/', views.notification_settings, name='notificaciones'),
    path('login/',     views.login_view,          name='login'),
    path('logout/',    views.logout_view,         name='logout'),
]
