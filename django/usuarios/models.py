from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class Usuario(AbstractUser):
    """Custom User model that extends Django's AbstractUser to match Flask model"""
    
    # Override username field to make it required and unique
    username = models.CharField(max_length=80, unique=True)
    email = models.EmailField(max_length=120, unique=True)
    
    # Additional fields from Flask model
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True, null=True)
    tipo_usuario = models.CharField(
        max_length=20, 
        choices=[('master', 'Master'), ('restrito', 'Restrito')],
        default='restrito'
    )
    criado_em = models.DateTimeField(default=timezone.now)
    ativo = models.BooleanField(default=True)
    
    # Permissions for restricted users
    pode_cadastrar_cliente = models.BooleanField(default=False)
    pode_cadastrar_funcionario = models.BooleanField(default=False)
    pode_cadastrar_cargo = models.BooleanField(default=False)
    pode_agendar = models.BooleanField(default=True)
    pode_ver_agendamentos = models.BooleanField(default=True)
    pode_ver_relatorios = models.BooleanField(default=False)

    # Override the is_active field to use our ativo field
    @property
    def is_active(self):
        return self.ativo

    def is_master(self):
        """Check if user is master"""
        return self.tipo_usuario == 'master'

    def is_funcionario(self):
        """Check if user is an employee"""
        return hasattr(self, 'perfil_funcionario')

    def __str__(self):
        return f'{self.username} - {self.nome}'

    class Meta:
        db_table = 'usuarios'
        verbose_name = 'Usuário'
        verbose_name_plural = 'Usuários'


class Cargo(models.Model):
    """Position/Role model"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.nome

    class Meta:
        db_table = 'cargos'
        verbose_name = 'Cargo'
        verbose_name_plural = 'Cargos'


class Servico(models.Model):
    """Service model"""
    nome = models.CharField(max_length=100, unique=True)
    descricao = models.TextField(blank=True, null=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    duracao_minutos = models.IntegerField()
    ativo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nome} - R$ {self.preco}'

    class Meta:
        db_table = 'servicos'
        verbose_name = 'Serviço'
        verbose_name_plural = 'Serviços'


class Funcionario(models.Model):
    """Employee model"""
    usuario = models.OneToOneField(
        Usuario, 
        on_delete=models.CASCADE, 
        related_name='perfil_funcionario'
    )
    cargo = models.ForeignKey(
        Cargo, 
        on_delete=models.CASCADE, 
        related_name='funcionarios'
    )
    data_contratacao = models.DateField(default=timezone.now)
    ativo = models.BooleanField(default=True)
    criado_em = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.usuario.nome} - {self.cargo.nome}'

    class Meta:
        db_table = 'funcionarios'
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'


class LogAuditoria(models.Model):
    """Audit log model"""
    usuario = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='logs_auditoria'
    )
    acao = models.CharField(max_length=100)
    tabela = models.CharField(max_length=50)
    registro_id = models.IntegerField(null=True, blank=True)
    valores_antigos = models.TextField(blank=True, null=True)
    valores_novos = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f'{self.acao} em {self.tabela}'

    class Meta:
        db_table = 'logs_auditoria'
        verbose_name = 'Log de Auditoria'
        verbose_name_plural = 'Logs de Auditoria'
