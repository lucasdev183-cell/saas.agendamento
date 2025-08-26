from django.db import models
from django.utils import timezone


class ConfiguracaoEmpresa(models.Model):
    """Company configuration model"""
    nome_empresa = models.CharField(max_length=200, default='JT Sistemas')
    logo_path = models.CharField(max_length=500, blank=True, null=True)
    whatsapp_token = models.CharField(max_length=500, blank=True, null=True)
    whatsapp_phone_id = models.CharField(max_length=100, blank=True, null=True)
    whatsapp_webhook_verify_token = models.CharField(max_length=200, blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'Configuração - {self.nome_empresa}'

    class Meta:
        db_table = 'configuracao_empresa'
        verbose_name = 'Configuração da Empresa'
        verbose_name_plural = 'Configurações da Empresa'
