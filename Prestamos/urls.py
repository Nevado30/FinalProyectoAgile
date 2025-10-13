from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'prestamos'

urlpatterns = [
    path('', login_required(views.lista_prestamos), name='lista'),
    path('<int:prestamo_id>/pagos/', login_required(views.pagos_por_prestamo), name='pagos'),
]
