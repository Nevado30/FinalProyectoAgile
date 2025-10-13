from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

app_name = 'persona'

urlpatterns = [
    path('', login_required(views.lista_personas), name='lista'),
    path('<int:persona_id>/prestamos/', login_required(views.prestamos_por_persona), name='prestamos'),
]
