from django.urls import path
from . import views

app_name = 'persona'

urlpatterns = [
    path('', views.lista_personas, name='lista'),
    path('<int:persona_id>/prestamos/', views.prestamos_por_persona, name='prestamos'),
]
