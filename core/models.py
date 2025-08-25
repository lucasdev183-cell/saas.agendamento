from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class Usuario(AbstractUser):
    """Modelo de usuário customizado baseado no AbstractUser do Django"""
    TIPO_USUARIO_CHOICES = [
        ('master', 'Master'),
        ('restrito', 'Restrito'),
    ]
    
    # Campos customizados
    tipo_usuario = models.CharField(
        max_length=20, 
        choices=TIPO_USUARIO_CHOICES, 
        default='restrito'
    )
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now)
    ativo = models.BooleanField(default=True)
    
    # Permissões específicas para usuários restritos
    pode_cadastrar_cliente = models.BooleanField(default=False)
    pode_cadastrar_funcionario = models.BooleanField(default=False)
    pode_cadastrar_cargo = models.BooleanField(default=False)
    pode_agendar = models.BooleanField(default=True)
    pode_ver_agendamentos = models.BooleanField(default=True)
    pode_ver_relatorios = models.BooleanField(default=False)
    
    def is_master(self):
        return self.tipo_usuario == 'master'
    
    def is_funcionario(self):
        return hasattr(self, 'perfil_funcionario') and self.perfil_funcionario is not None
    
    def __str__(self):
        return f'{self.nome} ({self.username})'
    
    class Meta:
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class Cargo(models.Model):
    """Modelo para cargos dos funcionários"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return self.nome
    
    class Meta:
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'


class Servico(models.Model):
    """Modelo para serviços oferecidos"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    duracao_minutos = models.PositiveIntegerField()
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f'{self.nome} - R$ {self.preco}'
    
    class Meta:
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'


class Funcionario(models.Model):
    """Modelo para funcionários (perfil adicional de usuário)"""
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='perfil_funcionario'
    )
    cargo = models.ForeignKey(
        Cargo, 
        on_delete=models.PROTECT,
        related_name='funcionarios'
    )
    data_contratacao = models.DateField(default=timezone.now)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'{self.usuario.nome} - {self.cargo.nome}'
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'


class Agendamento(models.Model):
    """Modelo para agendamentos"""
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name='agendamentos_como_cliente'
    )
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='agendamentos'
    )
    servico = models.ForeignKey(
        Servico,
        on_delete=models.PROTECT,
        related_name='agendamentos',
        null=True,
        blank=True
    )
    data_agendamento = models.DateTimeField()
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='agendado'
    )
    observacoes = models.TextField(blank=True, null=True)
    # Campo para compatibilidade com sistema antigo
    servico_texto = models.CharField(max_length=200, blank=True, null=True)
    duracao_minutos = models.PositiveIntegerField(default=60)
    criado_em = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f'Agendamento {self.id} - {self.cliente.nome}'
    
    class Meta:
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
        ordering = ['-data_agendamento']


class LogAuditoria(models.Model):
    """Modelo para logs de auditoria"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    acao = models.CharField(max_length=100)
    tabela = models.CharField(max_length=50)
    registro_id = models.PositiveIntegerField(null=True, blank=True)
    valores_antigos = models.TextField(blank=True, null=True)
    valores_novos = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    def __str__(self):
        return f'Log: {self.acao} em {self.tabela}'
    
    class Meta:
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
        ordering = ['-timestamp']


class ConfiguracaoEmpresa(models.Model):
    """Modelo para configurações da empresa"""
    nome_empresa = models.CharField(max_length=200, default='JT Sistemas')
    logo_path = models.CharField(max_length=500, blank=True, null=True)
    whatsapp_token = models.CharField(max_length=500, blank=True, null=True)
    whatsapp_phone_id = models.CharField(max_length=100, blank=True, null=True)
    whatsapp_webhook_verify_token = models.CharField(max_length=200, blank=True, null=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.nome_empresa
    
    class Meta:
        verbose_name = 'Configuração da Empresa'
        verbose_name_plural = 'Configurações da Empresa'