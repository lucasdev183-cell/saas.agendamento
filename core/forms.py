from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Usuario, Cargo, Funcionario, Servico, Agendamento, ConfiguracaoEmpresa


class LoginForm(AuthenticationForm):
    """Formulário de login personalizado"""
    username = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário'
        }),
        label='Usuário'
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        }),
        label='Senha'
    )


class CadastroUsuarioForm(UserCreationForm):
    """Formulário para cadastro de usuários"""
    nome = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Nome Completo'
    )
    email = forms.EmailField(
        max_length=120,
        widget=forms.EmailInput(attrs={'class': 'form-control'}),
        label='Email'
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'}),
        label='Telefone'
    )
    tipo_usuario = forms.ChoiceField(
        choices=[('restrito', 'Usuário Restrito')],
        initial='restrito',
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Tipo de Usuário'
    )
    
    # Permissões para usuários restritos
    pode_cadastrar_cliente = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Cadastrar Clientes'
    )
    pode_cadastrar_funcionario = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Cadastrar Funcionários'
    )
    pode_cadastrar_cargo = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Cadastrar Cargos'
    )
    pode_agendar = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Agendar'
    )
    pode_ver_agendamentos = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Ver Agendamentos'
    )
    pode_ver_relatorios = forms.BooleanField(
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Pode Ver Relatórios'
    )

    class Meta:
        model = Usuario
        fields = ('username', 'email', 'nome', 'telefone', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Email já está em uso.')
        return email


class UsuarioEditForm(forms.ModelForm):
    """Formulário para edição de usuários"""
    ativo = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label='Ativo'
    )

    class Meta:
        model = Usuario
        fields = [
            'email', 'nome', 'telefone', 'ativo',
            'pode_cadastrar_cliente', 'pode_cadastrar_funcionario',
            'pode_cadastrar_cargo', 'pode_agendar', 'pode_ver_agendamentos',
            'pode_ver_relatorios'
        ]
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
            'pode_cadastrar_cliente': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_cadastrar_funcionario': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_cadastrar_cargo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_agendar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_ver_agendamentos': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'pode_ver_relatorios': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class CadastroClienteForm(forms.ModelForm):
    """Formulário para cadastro de clientes (usuários sem senha)"""
    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'telefone']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email']
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Email já está em uso.')
        return email

    def save(self, commit=True):
        cliente = super().save(commit=False)
        cliente.username = cliente.email  # Username será o email
        cliente.tipo_usuario = 'restrito'
        cliente.set_unusable_password()  # Cliente não tem senha
        if commit:
            cliente.save()
        return cliente


class FuncionarioForm(forms.ModelForm):
    """Formulário para cadastro de funcionários"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Usuários disponíveis (ativos e que não são funcionários)
        self.fields['usuario'].queryset = Usuario.objects.filter(
            ativo=True,
            perfil_funcionario__isnull=True
        )
        # Todos os cargos
        self.fields['cargo'].queryset = Cargo.objects.all()

    class Meta:
        model = Funcionario
        fields = ['usuario', 'cargo']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-control'}),
            'cargo': forms.Select(attrs={'class': 'form-control'}),
        }


class CargoForm(forms.ModelForm):
    """Formulário para cadastro de cargos"""
    class Meta:
        model = Cargo
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        if Cargo.objects.filter(nome=nome).exists():
            raise ValidationError('Já existe um cargo com este nome.')
        return nome


class ServicoForm(forms.ModelForm):
    """Formulário para cadastro de serviços"""
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'preco', 'duracao_minutos', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nome(self):
        nome = self.cleaned_data['nome']
        if Servico.objects.filter(nome=nome).exists():
            raise ValidationError('Já existe um serviço com este nome.')
        return nome


class AgendamentoForm(forms.ModelForm):
    """Formulário para criar agendamentos"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Clientes (usuários restritos que não são funcionários)
        self.fields['cliente'].queryset = Usuario.objects.filter(
            ativo=True,
            tipo_usuario='restrito',
            perfil_funcionario__isnull=True
        )
        # Funcionários ativos
        self.fields['funcionario'].queryset = Funcionario.objects.filter(ativo=True)
        # Serviços ativos
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True)

    class Meta:
        model = Agendamento
        fields = ['cliente', 'funcionario', 'servico', 'data_agendamento', 'observacoes']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'funcionario': forms.Select(attrs={'class': 'form-control'}),
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'data_agendamento': forms.DateTimeInput(
                attrs={'class': 'form-control', 'type': 'datetime-local'}
            ),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class AtualizarStatusAgendamentoForm(forms.ModelForm):
    """Formulário para atualizar status de agendamentos"""
    class Meta:
        model = Agendamento
        fields = ['status', 'observacoes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ConfiguracaoBotWhatsAppForm(forms.ModelForm):
    """Formulário para configuração do WhatsApp"""
    class Meta:
        model = ConfiguracaoEmpresa
        fields = ['whatsapp_token', 'whatsapp_phone_id', 'whatsapp_webhook_verify_token']
        widgets = {
            'whatsapp_token': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_phone_id': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_webhook_verify_token': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'whatsapp_token': 'Token de Acesso do WhatsApp',
            'whatsapp_phone_id': 'ID do Telefone',
            'whatsapp_webhook_verify_token': 'Token de Verificação do Webhook',
        }


class ConfiguracaoEmpresaForm(forms.ModelForm):
    """Formulário para configuração da empresa"""
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        label='Logo da Empresa'
    )
    
    class Meta:
        model = ConfiguracaoEmpresa
        fields = ['nome_empresa']
        widgets = {
            'nome_empresa': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'nome_empresa': 'Nome da Empresa',
        }