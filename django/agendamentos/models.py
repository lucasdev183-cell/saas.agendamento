from django.db import models
from django.utils import timezone
from usuarios.models import Usuario, Funcionario


class Agendamento(models.Model):
    """Appointment model"""
    
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='agendamentos_cliente'
    )
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.CASCADE,
        related_name='agendamentos'
    )
    data_agendamento = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='agendado'
    )
    observacoes = models.TextField(blank=True, null=True)
    servico = models.CharField(max_length=200, blank=True, null=True)  # Keep for backward compatibility
    duracao_minutos = models.IntegerField(default=60)
    criado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'Agendamento {self.id} - {self.cliente.nome}'

    class Meta:
        db_table = 'agendamentos'
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data_agendamento']
