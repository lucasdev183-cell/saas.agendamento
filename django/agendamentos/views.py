from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.utils import timezone

from .models import Agendamento
from .forms import AgendamentoForm, AtualizarStatusAgendamentoForm
from usuarios.models import Usuario, Funcionario


@login_required
def agendamentos(request):
    """Appointments list view"""
    if not (request.user.is_master() or request.user.pode_ver_agendamentos):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    # Filter appointments based on user type
    if request.user.is_master():
        agendamentos_list = Agendamento.objects.all()
    elif request.user.is_funcionario():
        funcionario = getattr(request.user, 'perfil_funcionario', None)
        if funcionario:
            agendamentos_list = Agendamento.objects.filter(funcionario=funcionario)
        else:
            agendamentos_list = Agendamento.objects.none()
    else:
        agendamentos_list = Agendamento.objects.filter(cliente=request.user)
    
    # Apply search filter if provided
    search = request.GET.get('search', '')
    if search:
        agendamentos_list = agendamentos_list.filter(
            Q(cliente__nome__icontains=search) |
            Q(funcionario__usuario__nome__icontains=search) |
            Q(servico__icontains=search)
        )
    
    agendamentos_list = agendamentos_list.order_by('-data_agendamento')
    
    return render(request, 'agendamentos/agendamentos.html', {
        'agendamentos': agendamentos_list,
        'search': search
    })


@login_required
def agendar(request):
    """Create appointment view"""
    if not (request.user.is_master() or request.user.pode_agendar):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            # Set service name if service_id was selected
            servico_id = form.cleaned_data.get('servico_id')
            if servico_id:
                agendamento.servico = servico_id.nome
                agendamento.duracao_minutos = servico_id.duracao_minutos
            agendamento.save()
            messages.success(request, 'Agendamento criado com sucesso!')
            return redirect('agendamentos:agendamentos')
    else:
        form = AgendamentoForm()
    
    return render(request, 'agendamentos/agendar.html', {'form': form})


@login_required
def agendamento_atualizar(request, agendamento_id):
    """Update appointment status"""
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    
    # Check permissions
    if not (request.user.is_master() or 
            (request.user.is_funcionario() and 
             getattr(request.user, 'perfil_funcionario', None) == agendamento.funcionario)):
        messages.error(request, 'Acesso negado.')
        return redirect('agendamentos:agendamentos')
    
    if request.method == 'POST':
        form = AtualizarStatusAgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Status do agendamento atualizado com sucesso!')
            return redirect('agendamentos:agendamentos')
    else:
        form = AtualizarStatusAgendamentoForm(instance=agendamento)
    
    return render(request, 'agendamentos/agendamento_form.html', {
        'form': form,
        'agendamento': agendamento
    })


@login_required
def agendamento_editar(request, agendamento_id):
    """Edit appointment view"""
    agendamento = get_object_or_404(Agendamento, id=agendamento_id)
    
    # Check permissions
    if not (request.user.is_master() or 
            (request.user.is_funcionario() and 
             getattr(request.user, 'perfil_funcionario', None) == agendamento.funcionario)):
        messages.error(request, 'Acesso negado.')
        return redirect('agendamentos:agendamentos')
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            agendamento = form.save(commit=False)
            # Update service info if changed
            servico_id = form.cleaned_data.get('servico_id')
            if servico_id:
                agendamento.servico = servico_id.nome
                agendamento.duracao_minutos = servico_id.duracao_minutos
            agendamento.save()
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('agendamentos:agendamentos')
    else:
        form = AgendamentoForm(instance=agendamento)
    
    return render(request, 'agendamentos/agendamento_form.html', {
        'form': form,
        'agendamento': agendamento
    })


@login_required
def relatorios(request):
    """Reports view"""
    if not (request.user.is_master() or request.user.pode_ver_relatorios):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    # Basic statistics for reports
    stats = {
        'total_agendamentos': Agendamento.objects.count(),
        'agendamentos_concluidos': Agendamento.objects.filter(status='concluido').count(),
        'agendamentos_cancelados': Agendamento.objects.filter(status='cancelado').count(),
        'agendamentos_hoje': Agendamento.objects.filter(
            data_agendamento__date=timezone.now().date()
        ).count(),
    }
    
    # Recent appointments for the table
    agendamentos_recentes = Agendamento.objects.order_by('-criado_em')[:20]
    
    return render(request, 'agendamentos/relatorios.html', {
        'stats': stats,
        'agendamentos_recentes': agendamentos_recentes
    })
