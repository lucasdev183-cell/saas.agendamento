from django.urls import path
from . import views

app_name = 'agendamentos'

urlpatterns = [
    path('', views.agendamentos, name='agendamentos'),
    path('agendar/', views.agendar, name='agendar'),
    path('<int:agendamento_id>/atualizar/', views.agendamento_atualizar, name='agendamento_atualizar'),
    path('<int:agendamento_id>/editar/', views.agendamento_editar, name='agendamento_editar'),
    path('relatorios/', views.relatorios, name='relatorios'),
]