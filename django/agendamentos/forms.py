from django import forms
from .models import Agendamento
from usuarios.models import Usuario, Funcionario, Servico


class AgendamentoForm(forms.ModelForm):
    """Appointment form"""
    cliente = forms.ModelChoiceField(
        queryset=Usuario.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    funcionario = forms.ModelChoiceField(
        queryset=Funcionario.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    servico_id = forms.ModelChoiceField(
        queryset=Servico.objects.filter(ativo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Serviço'
    )
    data_agendamento = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={
            'class': 'form-control',
            'type': 'datetime-local'
        })
    )
    observacoes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
    )

    class Meta:
        model = Agendamento
        fields = ['cliente', 'funcionario', 'data_agendamento', 'observacoes']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show clients (restricted users without employee profile)
        self.fields['cliente'].queryset = Usuario.objects.filter(
            ativo=True,
            tipo_usuario='restrito',
            perfil_funcionario__isnull=True
        )
        # Only show active employees
        self.fields['funcionario'].queryset = Funcionario.objects.filter(ativo=True)


class AtualizarStatusAgendamentoForm(forms.ModelForm):
    """Update appointment status form"""
    
    class Meta:
        model = Agendamento
        fields = ['status', 'observacoes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }