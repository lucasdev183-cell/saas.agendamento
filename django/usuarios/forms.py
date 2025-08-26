from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Usuario, Cargo, Servico, Funcionario


class LoginForm(AuthenticationForm):
    """Login form"""
    username = forms.CharField(
        max_length=80,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Usuário'
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Senha'
        })
    )


class CadastroUsuarioForm(UserCreationForm):
    """User registration form"""
    nome = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        max_length=120,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    telefone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    tipo_usuario = forms.ChoiceField(
        choices=[('restrito', 'Usuário Restrito')],
        initial='restrito',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Permissions for restricted users
    pode_cadastrar_cliente = forms.BooleanField(required=False)
    pode_cadastrar_funcionario = forms.BooleanField(required=False)
    pode_cadastrar_cargo = forms.BooleanField(required=False)
    pode_agendar = forms.BooleanField(initial=True, required=False)
    pode_ver_agendamentos = forms.BooleanField(initial=True, required=False)
    pode_ver_relatorios = forms.BooleanField(required=False)

    class Meta:
        model = Usuario
        fields = ['username', 'email', 'nome', 'telefone', 'password1', 'password2', 
                 'tipo_usuario', 'pode_cadastrar_cliente', 'pode_cadastrar_funcionario',
                 'pode_cadastrar_cargo', 'pode_agendar', 'pode_ver_agendamentos', 
                 'pode_ver_relatorios']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Email já cadastrado.')
        return email

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if Usuario.objects.filter(username=username).exists():
            raise ValidationError('Nome de usuário já existe.')
        return username


class UsuarioEditForm(forms.ModelForm):
    """User edit form"""
    
    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'telefone', 'ativo', 'pode_cadastrar_cliente',
                 'pode_cadastrar_funcionario', 'pode_cadastrar_cargo', 'pode_agendar',
                 'pode_ver_agendamentos', 'pode_ver_relatorios']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CadastroClienteForm(forms.ModelForm):
    """Client registration form"""
    
    class Meta:
        model = Usuario
        fields = ['email', 'nome', 'telefone']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError('Email já cadastrado.')
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set default values for clients
        user.username = user.email  # Use email as username
        user.tipo_usuario = 'restrito'
        user.set_unusable_password()  # Clients don't have passwords
        if commit:
            user.save()
        return user


class FuncionarioForm(forms.ModelForm):
    """Employee form"""
    usuario = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    cargo = forms.ModelChoiceField(
        queryset=Cargo.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Funcionario
        fields = ['usuario', 'cargo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show users that are not already employees
        self.fields['usuario'].queryset = Usuario.objects.filter(
            ativo=True,
            perfil_funcionario__isnull=True
        )


class CargoForm(forms.ModelForm):
    """Position form"""
    
    class Meta:
        model = Cargo
        fields = ['nome', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ServicoForm(forms.ModelForm):
    """Service form"""
    
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'preco', 'duracao_minutos', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'duracao_minutos': forms.NumberInput(attrs={'class': 'form-control'}),
        }