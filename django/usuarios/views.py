from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count
from django.utils import timezone
from datetime import datetime, date
from functools import wraps

from .models import Usuario, Cargo, Servico, Funcionario
from .forms import (LoginForm, CadastroUsuarioForm, UsuarioEditForm, 
                   CadastroClienteForm, FuncionarioForm, CargoForm, ServicoForm)
from agendamentos.models import Agendamento
from configuracoes.models import ConfiguracaoEmpresa


def master_required(view_func):
    """Decorator to require master user"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_master():
            messages.error(request, 'Acesso negado. Apenas usuários master podem acessar esta página.')
            return redirect('usuarios:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def index(request):
    """Index page - redirects to dashboard if authenticated, otherwise login"""
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')
    return redirect('usuarios:login')


def login_view(request):
    """Login view"""
    if request.user.is_authenticated:
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.ativo:
                login(request, user)
                messages.success(request, 'Login realizado com sucesso!')
                next_page = request.GET.get('next')
                return redirect(next_page or 'usuarios:dashboard')
            else:
                messages.error(request, 'Usuário inativo.')
        else:
            messages.error(request, 'Usuário ou senha inválidos.')
    else:
        form = LoginForm()
    
    return render(request, 'usuarios/login.html', {'form': form})


@login_required
def logout_view(request):
    """Logout view"""
    logout(request)
    messages.info(request, 'Logout realizado com sucesso!')
    return redirect('usuarios:login')


@login_required
def dashboard(request):
    """Dashboard view with statistics"""
    stats = {}
    config = ConfiguracaoEmpresa.objects.first()
    
    if request.user.is_master():
        stats = {
            'total_usuarios': Usuario.objects.count(),
            'total_funcionarios': Funcionario.objects.count(),
            'total_agendamentos': Agendamento.objects.count(),
            'agendamentos_pendentes': Agendamento.objects.filter(status='agendado').count(),
            'agendamentos_hoje': Agendamento.objects.filter(
                data_agendamento__date=timezone.now().date()
            ).count()
        }
        agendamentos_recentes = Agendamento.objects.order_by('-criado_em')[:5]
    
    elif request.user.is_funcionario():
        funcionario = getattr(request.user, 'perfil_funcionario', None)
        if funcionario:
            stats = {
                'meus_agendamentos_hoje': Agendamento.objects.filter(
                    funcionario=funcionario,
                    data_agendamento__date=timezone.now().date()
                ).count(),
                'meus_agendamentos_pendentes': Agendamento.objects.filter(
                    funcionario=funcionario,
                    status='agendado'
                ).count()
            }
            agendamentos_recentes = Agendamento.objects.filter(
                funcionario=funcionario
            ).order_by('-data_agendamento')[:5]
        else:
            agendamentos_recentes = []
    
    else:
        stats = {
            'meus_agendamentos': Agendamento.objects.filter(cliente=request.user).count(),
            'meus_proximos_agendamentos': Agendamento.objects.filter(
                cliente=request.user,
                data_agendamento__gt=timezone.now(),
                status='agendado'
            ).count()
        }
        agendamentos_recentes = Agendamento.objects.filter(
            cliente=request.user
        ).order_by('-data_agendamento')[:5]
    
    return render(request, 'usuarios/dashboard.html', {
        'stats': stats,
        'agendamentos_recentes': agendamentos_recentes,
        'config': config
    })


@login_required
@master_required
def usuarios_pesquisar(request):
    """Users search/list view"""
    search = request.GET.get('search', '')
    usuarios = Usuario.objects.all()
    
    if search:
        usuarios = usuarios.filter(
            Q(nome__icontains=search) |
            Q(username__icontains=search) |
            Q(email__icontains=search)
        )
    
    return render(request, 'usuarios/usuarios_pesquisa.html', {
        'usuarios': usuarios,
        'search': search
    })


@login_required
@master_required
def usuario_inserir(request):
    """User creation view"""
    if request.method == 'POST':
        form = CadastroUsuarioForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.ativo = True
            user.save()
            messages.success(request, 'Usuário criado com sucesso!')
            return redirect('usuarios:usuarios_pesquisar')
    else:
        form = CadastroUsuarioForm()
    
    return render(request, 'usuarios/usuario_inserir.html', {'form': form})


@login_required
@master_required
def usuario_visualizar(request, usuario_id):
    """User detail view"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    return render(request, 'usuarios/usuario_visualizar.html', {'usuario': usuario})


@login_required
@master_required
def usuario_editar(request, usuario_id):
    """User edit view"""
    usuario = get_object_or_404(Usuario, id=usuario_id)
    
    if request.method == 'POST':
        form = UsuarioEditForm(request.POST, instance=usuario)
        if form.is_valid():
            form.save()
            messages.success(request, 'Usuário atualizado com sucesso!')
            return redirect('usuarios:usuario_visualizar', usuario_id=usuario.id)
    else:
        form = UsuarioEditForm(instance=usuario)
    
    return render(request, 'usuarios/usuario_editar.html', {
        'form': form,
        'usuario': usuario
    })


@login_required
def clientes_pesquisar(request):
    """Clients search/list view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_cliente):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    search = request.GET.get('search', '')
    clientes = Usuario.objects.filter(
        tipo_usuario='restrito',
        perfil_funcionario__isnull=True
    )
    
    if search:
        clientes = clientes.filter(
            Q(nome__icontains=search) |
            Q(email__icontains=search) |
            Q(telefone__icontains=search)
        )
    
    return render(request, 'usuarios/clientes_pesquisa.html', {
        'clientes': clientes,
        'search': search
    })


@login_required
def cliente_inserir(request):
    """Client creation view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_cliente):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = CadastroClienteForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cliente criado com sucesso!')
            return redirect('usuarios:clientes_pesquisar')
    else:
        form = CadastroClienteForm()
    
    return render(request, 'usuarios/cliente_inserir.html', {'form': form})


@login_required
def funcionarios(request):
    """Employees list view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_funcionario):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    funcionarios = Funcionario.objects.filter(ativo=True)
    return render(request, 'usuarios/funcionarios.html', {
        'funcionarios': funcionarios
    })


@login_required
def funcionario_criar(request):
    """Employee creation view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_funcionario):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = FuncionarioForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Funcionário criado com sucesso!')
            return redirect('usuarios:funcionarios')
    else:
        form = FuncionarioForm()
    
    return render(request, 'usuarios/funcionario_inserir.html', {'form': form})


@login_required
def cargos_main(request):
    """Positions main view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_cargo):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    cargos = Cargo.objects.all()
    return render(request, 'usuarios/cargos.html', {'cargos': cargos})


@login_required
def cargo_inserir(request):
    """Position creation view"""
    if not (request.user.is_master() or request.user.pode_cadastrar_cargo):
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = CargoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cargo criado com sucesso!')
            return redirect('usuarios:cargos_main')
    else:
        form = CargoForm()
    
    return render(request, 'usuarios/cargo_form.html', {'form': form})


@login_required
def servicos_main(request):
    """Services main view"""
    if not request.user.is_master():
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    servicos = Servico.objects.all()
    return render(request, 'usuarios/servicos.html', {'servicos': servicos})


@login_required
def servico_inserir(request):
    """Service creation view"""
    if not request.user.is_master():
        messages.error(request, 'Acesso negado.')
        return redirect('usuarios:dashboard')
    
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Serviço criado com sucesso!')
            return redirect('usuarios:servicos_main')
    else:
        form = ServicoForm()
    
    return render(request, 'usuarios/servico_inserir.html', {'form': form})
