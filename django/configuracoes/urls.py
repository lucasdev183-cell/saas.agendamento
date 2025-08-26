from django.urls import path
from . import views

app_name = 'configuracoes'

urlpatterns = [
    path('', views.configuracoes, name='configuracoes'),
    path('bot-whatsapp/', views.bot_whatsapp, name='bot_whatsapp'),
    path('bot-whatsapp/api/', views.bot_whatsapp_api, name='bot_whatsapp_api'),
    path('bot-whatsapp/configurar/', views.bot_whatsapp_configurar, name='bot_whatsapp_configurar'),
    path('bot-whatsapp/fluxo/', views.bot_whatsapp_fluxo, name='bot_whatsapp_fluxo'),
    path('bot-whatsapp/geral/', views.bot_whatsapp_geral, name='bot_whatsapp_geral'),
]