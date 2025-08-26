from django import forms
from .models import ConfiguracaoEmpresa


class ConfiguracaoEmpresaForm(forms.ModelForm):
    """Company configuration form"""
    logo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = ConfiguracaoEmpresa
        fields = ['nome_empresa', 'logo']
        widgets = {
            'nome_empresa': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.cleaned_data.get('logo'):
            # Handle file upload
            logo_file = self.cleaned_data['logo']
            # Save file and update logo_path
            instance.logo_path = logo_file.name
        if commit:
            instance.save()
        return instance


class ConfiguracaoBotWhatsAppForm(forms.ModelForm):
    """WhatsApp Bot configuration form"""
    
    class Meta:
        model = ConfiguracaoEmpresa
        fields = ['whatsapp_token', 'whatsapp_phone_id', 'whatsapp_webhook_verify_token']
        widgets = {
            'whatsapp_token': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_phone_id': forms.TextInput(attrs={'class': 'form-control'}),
            'whatsapp_webhook_verify_token': forms.TextInput(attrs={'class': 'form-control'}),
        }