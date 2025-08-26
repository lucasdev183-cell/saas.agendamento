from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.files.storage import default_storage
import os

from .models import ConfiguracaoEmpresa
from .forms import ConfiguracaoEmpresaForm, ConfiguracaoBotWhatsAppForm
from usuarios.views import master_required


@login_required
@master_required
def configuracoes(request):
    """General configuration view"""
    config, created = ConfiguracaoEmpresa.objects.get_or_create(
        id=1,
        defaults={'nome_empresa': 'JT Sistemas'}
    )
    
    if request.method == 'POST':
        form = ConfiguracaoEmpresaForm(request.POST, request.FILES, instance=config)
        if form.is_valid():
            if 'logo' in request.FILES:
                # Handle logo upload
                logo_file = request.FILES['logo']
                filename = default_storage.save(f'uploads/{logo_file.name}', logo_file)
                config.logo_path = filename
            form.save()
            messages.success(request, 'Configurações atualizadas com sucesso!')
            return redirect('configuracoes:configuracoes')
    else:
        form = ConfiguracaoEmpresaForm(instance=config)
    
    return render(request, 'configuracoes/configuracoes.html', {
        'form': form,
        'config': config
    })


@login_required
@master_required
def bot_whatsapp(request):
    """WhatsApp bot main view"""
    return render(request, 'configuracoes/bot_whatsapp.html')


@login_required
@master_required
def bot_whatsapp_api(request):
    """WhatsApp bot API configuration"""
    config, created = ConfiguracaoEmpresa.objects.get_or_create(
        id=1,
        defaults={'nome_empresa': 'JT Sistemas'}
    )
    
    if request.method == 'POST':
        form = ConfiguracaoBotWhatsAppForm(request.POST, instance=config)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações do WhatsApp Bot atualizadas com sucesso!')
            return redirect('configuracoes:bot_whatsapp_api')
    else:
        form = ConfiguracaoBotWhatsAppForm(instance=config)
    
    return render(request, 'configuracoes/bot_config.html', {
        'form': form,
        'config': config
    })


@login_required
@master_required
def bot_whatsapp_configurar(request):
    """WhatsApp bot configuration view"""
    return render(request, 'configuracoes/bot_geral.html')


@login_required
@master_required
def bot_whatsapp_fluxo(request):
    """WhatsApp bot flow configuration"""
    return render(request, 'configuracoes/bot_fluxo.html')


@login_required
@master_required
def bot_whatsapp_geral(request):
    """WhatsApp bot general settings"""
    return render(request, 'configuracoes/bot_geral.html')
