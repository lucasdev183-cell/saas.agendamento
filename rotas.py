from flask import render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from aplicacao import app, db
from modelos import (Usuario, Funcionario, Cargo, Agendamento, LogAuditoria, ConfiguracaoEmpresa, 
                     Servico, CategoriaServico, EspecialidadeFuncionario)
from formularios import (LoginForm, CadastroUsuarioForm, CadastroClienteForm, FuncionarioForm,
                         CargoForm, AgendamentoForm, AtualizarStatusAgendamentoForm,
                         ConfiguracaoBotWhatsAppForm, ConfiguracaoEmpresaForm, ServicoForm, UsuarioEditForm,
                         CategoriaServicoForm, EspecialidadeFuncionarioForm)
from datetime import datetime, timedelta
from sqlalchemy import and_, or_, func
from werkzeug.security import generate_password_hash
from werkzeug.utils import secure_filename
import os
import re
import json
import zipfile
import tempfile
from io import BytesIO
import csv
from flask import send_file, make_response

# ========================================
# SISTEMA DE VALIDAÇÕES E INTEGRIDADE
# ========================================

def validate_unique_email(email, exclude_user_id=None):
    """Valida se o email é único no sistema"""
    query = Usuario.query.filter_by(email=email)
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.first() is None

def validate_unique_username(username, exclude_user_id=None):
    """Valida se o username é único no sistema"""
    query = Usuario.query.filter_by(username=username)
    if exclude_user_id:
        query = query.filter(Usuario.id != exclude_user_id)
    return query.first() is None

def validate_unique_cargo_name(nome, exclude_cargo_id=None):
    """Valida se o nome do cargo é único"""
    query = Cargo.query.filter_by(nome=nome)
    if exclude_cargo_id:
        query = query.filter(Cargo.id != exclude_cargo_id)
    return query.first() is None

def validate_unique_servico_name(nome, exclude_servico_id=None):
    """Valida se o nome do serviço é único"""
    query = Servico.query.filter_by(nome=nome)
    if exclude_servico_id:
        query = query.filter(Servico.id != exclude_servico_id)
    return query.first() is None

def check_cargo_references(cargo_id):
    """Verifica se o cargo tem referências em outras tabelas"""
    funcionarios_count = Funcionario.query.filter_by(cargo_id=cargo_id).count()
    return {
        'can_delete': funcionarios_count == 0,
        'references': {
            'funcionarios': funcionarios_count
        },
        'total_references': funcionarios_count
    }

def check_usuario_references(usuario_id):
    """Verifica se o usuário tem referências em outras tabelas"""
    funcionario_count = Funcionario.query.filter_by(usuario_id=usuario_id).count()
    agendamentos_count = Agendamento.query.filter_by(cliente_id=usuario_id).count()
    
    total_references = funcionario_count + agendamentos_count
    
    return {
        'can_delete': total_references == 0,
        'references': {
            'funcionario': funcionario_count,
            'agendamentos': agendamentos_count
        },
        'total_references': total_references
    }

def check_servico_references(servico_id):
    """Verifica se o serviço tem referências em outras tabelas"""
    agendamentos_count = Agendamento.query.filter_by(servico_id=servico_id).count()
    
    return {
        'can_delete': agendamentos_count == 0,
        'references': {
            'agendamentos': agendamentos_count
        },
        'total_references': agendamentos_count
    }

def check_funcionario_references(funcionario_id):
    """Verifica se o funcionário tem referências em outras tabelas"""
    agendamentos_count = Agendamento.query.filter_by(funcionario_id=funcionario_id).count()
    
    return {
        'can_delete': agendamentos_count == 0,
        'references': {
            'agendamentos': agendamentos_count
        },
        'total_references': agendamentos_count
    }

def format_validation_errors(errors_dict):
    """Formata erros de validação para exibição"""
    formatted_errors = []
    for field, errors in errors_dict.items():
        for error in errors:
            formatted_errors.append(f"{field.title()}: {error}")
    return formatted_errors

# Decorator para verificar permissões
def master_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_master():
            flash('Acesso negado. Apenas usuários Master podem acessar esta página.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))
            
            if current_user.is_master():
                return f(*args, **kwargs)
            
            # Use getattr para verificar se a permissão existe e se é True
            if not getattr(current_user, permission, False):
                flash('Você não tem permissão para acessar esta página.', 'danger')
                return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    """
    Rota principal, redireciona para o dashboard se o usuário estiver autenticado.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    Rota para o login de usuários.
    """
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = (form.username.data or '').strip()
        password = form.password.data or ''
        # Fallback MASTER login (uppercase enforced)
        if username == 'MASTER' and password == 'MASTER123':
            usuario = Usuario.query.filter_by(username='MASTER').first()
            if not usuario:
                usuario = Usuario(
                    username='MASTER',
                    email='MASTER@EXAMPLE.COM',
                    nome='MASTER',
                    telefone='',
                    tipo_usuario='master',
                    ativo=True
                )
                usuario.set_password('MASTER123')
                db.session.add(usuario)
                db.session.commit()
            if usuario and usuario.ativo:
                login_user(usuario)
                flash('Login realizado com sucesso!', 'success')
                return redirect(url_for('dashboard'))
        # Fluxo padrão
        usuario = Usuario.query.filter_by(username=username).first()
        if usuario and usuario.check_password(password) and usuario.ativo:
            login_user(usuario)
            next_page = request.args.get('next')
            flash('Login realizado com sucesso!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        flash('Usuário ou senha inválidos.', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """
    Rota para o logout de usuários.
    """
    logout_user()
    flash('Logout realizado com sucesso!', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal, com estatísticas e agendamentos recentes.
    Os dados exibidos variam de acordo com o tipo de usuário.
    """
    stats = {}
    config = ConfiguracaoEmpresa.query.first()
    
    if current_user.is_master():
        stats = {
            'total_usuarios': Usuario.query.count(),
            'total_funcionarios': Funcionario.query.count(),
            'total_agendamentos': Agendamento.query.count(),
            'agendamentos_pendentes': Agendamento.query.filter_by(status='agendado').count(),
            'agendamentos_hoje': Agendamento.query.filter(
                func.date(Agendamento.data_agendamento) == datetime.utcnow().date()
            ).count()
        }
        agendamentos_recentes = Agendamento.query.order_by(Agendamento.criado_em.desc()).limit(5).all()
    
    elif current_user.is_funcionario():
        funcionario = Funcionario.query.filter_by(usuario_id=current_user.id).first()
        if funcionario:
            stats = {
                'meus_agendamentos_hoje': Agendamento.query.filter(
                    and_(
                        Agendamento.funcionario_id == funcionario.id,
                        func.date(Agendamento.data_agendamento) == datetime.utcnow().date()
                    )
                ).count(),
                'meus_agendamentos_pendentes': Agendamento.query.filter(
                    and_(
                        Agendamento.funcionario_id == funcionario.id,
                        Agendamento.status == 'agendado'
                    )
                ).count()
            }
            agendamentos_recentes = Agendamento.query.filter_by(funcionario_id=funcionario.id)\
                                                    .order_by(Agendamento.data_agendamento.desc()).limit(5).all()
        else:
            agendamentos_recentes = []
    
    else:
        stats = {
            'meus_agendamentos': Agendamento.query.filter_by(cliente_id=current_user.id).count(),
            'meus_proximos_agendamentos': Agendamento.query.filter(
                and_(
                    Agendamento.cliente_id == current_user.id,
                    Agendamento.data_agendamento > datetime.utcnow(),
                    Agendamento.status == 'agendado'
                )
            ).count()
        }
        agendamentos_recentes = Agendamento.query.filter_by(cliente_id=current_user.id)\
                                                .order_by(Agendamento.data_agendamento.desc()).limit(5).all()
    
    return render_template('dashboard.html', stats=stats, agendamentos_recentes=agendamentos_recentes, config=config)

@app.route('/cadastro')
@login_required
def cadastro():
    """
    Redireciona para o dashboard com menu lateral expandido.
    """
    return redirect(url_for('dashboard', expand_menu='cadastro'))

@app.route('/cadastro/usuario', methods=['GET'])
@login_required
@master_required
def cadastro_usuario():
    """
    Rota legada de cadastro de usuário. Redireciona para a tela de pesquisa/gerenciamento.
    """
    return redirect(url_for('usuarios_pesquisar', search=1))

@app.route('/cadastro/usuario/inserir', methods=['GET', 'POST'])
@login_required
@master_required
def usuario_inserir():
    """
    Rota para inserir um novo usuário com UI dedicada.
    """
    form = CadastroUsuarioForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('usuario_inserir.html', form=form)

        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('usuario_inserir.html', form=form)

        usuario = Usuario(
            username=form.username.data,
            email=form.email.data,
            nome=form.nome.data,
            telefone=form.telefone.data,
            tipo_usuario=form.tipo_usuario.data,
            ativo=True,
            pode_cadastrar_cliente=form.pode_cadastrar_cliente.data,
            pode_cadastrar_funcionario=form.pode_cadastrar_funcionario.data,
            pode_cadastrar_cargo=form.pode_cadastrar_cargo.data,
            pode_agendar=form.pode_agendar.data,
            pode_ver_agendamentos=form.pode_ver_agendamentos.data,
            pode_ver_relatorios=form.pode_ver_relatorios.data
        )
        usuario.set_password(form.password.data)

        db.session.add(usuario)
        db.session.commit()

        flash('Usuário cadastrado com sucesso!', 'success')
        return redirect(url_for('usuarios_pesquisar', search=1))

    return render_template('usuario_inserir.html', form=form)

@app.route('/cadastro/usuario/visualizar/<int:usuario_id>')
@login_required
@master_required
def usuario_visualizar(usuario_id):
    """
    Rota para visualizar detalhes de um usuário.
    """
    usuario = Usuario.query.get_or_404(usuario_id)
    return render_template('usuario_visualizar.html', usuario=usuario)

@app.route('/cadastro/usuario/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
@master_required
def usuario_editar(usuario_id):
    """
    Rota para editar um usuário existente.
    """
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioEditForm(obj=usuario)
    
    if form.validate_on_submit():
        usuario.username = form.username.data
        usuario.email = form.email.data
        usuario.nome = form.nome.data
        usuario.telefone = form.telefone.data
        usuario.pode_cadastrar_cliente = form.pode_cadastrar_cliente.data
        usuario.pode_cadastrar_funcionario = form.pode_cadastrar_funcionario.data
        usuario.pode_cadastrar_cargo = form.pode_cadastrar_cargo.data
        usuario.pode_agendar = form.pode_agendar.data
        usuario.pode_ver_agendamentos = form.pode_ver_agendamentos.data
        usuario.pode_ver_relatorios = form.pode_ver_relatorios.data
        
        if form.password.data:
            usuario.set_password(form.password.data)
        
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('usuarios_pesquisar', search=1))
    
    return render_template('usuario_editar.html', form=form, usuario=usuario)

# Pesquisa/Listagem de usuários no padrão de serviços
@app.route('/cadastro/usuarios/pesquisar', methods=['GET'])
@login_required
@master_required
def usuarios_pesquisar():
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    show_results = request.args.get('search') == '1'
    field = request.args.get('field', 'nome')

    base_query = Usuario.query.order_by(Usuario.nome)
    if query:
        if field == 'codigo' and query.isdigit():
            base_query = base_query.filter(Usuario.id == int(query))
        elif field == 'username':
            base_query = base_query.filter(Usuario.username.ilike(f'%{query}%'))
        elif field == 'email':
            base_query = base_query.filter(Usuario.email.ilike(f'%{query}%'))
        elif field == 'telefone':
            base_query = base_query.filter(Usuario.telefone.ilike(f'%{query}%'))
        else:
            base_query = base_query.filter(Usuario.nome.ilike(f'%{query}%'))

    usuarios = base_query.paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    return render_template('usuarios_pesquisa.html', usuarios=usuarios, query=query, per_page=per_page, show_results=show_results, field=field)

@app.route('/cadastro/clientes/pesquisar', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_cliente')
def clientes_pesquisar():
    """
    Pesquisa/lista clientes no padrão de serviços.
    """
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    # Exibir resultados somente quando o usuário clicar em Filtrar (submitted=1)
    show_results = request.args.get('submitted') == '1'

    base_query = Usuario.query.filter(
        and_(
            Usuario.tipo_usuario == 'restrito',
            Usuario.perfil_funcionario == None
        )
    ).order_by(Usuario.nome)

    field = request.args.get('field', 'nome')
    if query:
        if field == 'codigo' and query.isdigit():
            base_query = base_query.filter(Usuario.id == int(query))
        elif field == 'email':
            base_query = base_query.filter(Usuario.email.ilike(f"%{query}%"))
        elif field == 'telefone':
            base_query = base_query.filter(Usuario.telefone.ilike(f"%{query}%"))
        else:
            base_query = base_query.filter(Usuario.nome.ilike(f"%{query}%"))

    clientes = base_query.paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    return render_template('clientes_pesquisa.html', clientes=clientes, query=query, per_page=per_page, show_results=show_results, field=field)

@app.route('/cadastro/clientes/inserir', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_cliente')
def clientes_inserir():
    form = CadastroClienteForm()
    if form.validate_on_submit():
        # Verificar se email já existe
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('cliente_inserir.html', form=form)
        
        # Verificar CPF/CNPJ se fornecido
        if form.cpf_cnpj.data:
            cpf_cnpj_limpo = re.sub(r'[^0-9]', '', form.cpf_cnpj.data)
            if Usuario.query.filter_by(cpf_cnpj=cpf_cnpj_limpo).first():
                flash('CPF/CNPJ já cadastrado.', 'danger')
                return render_template('cliente_inserir.html', form=form)
        
        # Gerar username automaticamente a partir do nome
        base_username = (form.nome.data or '').strip().replace(' ', '').lower()
        base_username = re.sub(r'[^a-z0-9]', '', base_username)  # Remove caracteres especiais
        base_username = base_username[:12] or 'cliente'
        username = base_username
        suffix = 1
        while Usuario.query.filter_by(username=username).first() is not None:
            username = f"{base_username}{suffix}"
            suffix += 1

        usuario = Usuario(
            username=username,
            email=form.email.data,
            nome=form.nome.data,
            telefone=form.telefone.data,
            cpf_cnpj=re.sub(r'[^0-9]', '', form.cpf_cnpj.data) if form.cpf_cnpj.data else None,
            endereco=form.endereco.data,
            cidade=form.cidade.data,
            estado=form.estado.data,
            cep=re.sub(r'[^0-9]', '', form.cep.data) if form.cep.data else None,
            data_nascimento=form.data_nascimento.data,
            observacoes=form.observacoes.data,
            tipo_usuario='restrito',
            ativo=True
        )
        
        try:
            db.session.add(usuario)
            db.session.commit()
            
            # Log de auditoria
            log = LogAuditoria(
                usuario_id=current_user.id,
                acao='CREATE',
                tabela='usuarios',
                registro_id=usuario.id,
                valores_novos=f"Cliente: {usuario.nome} ({usuario.email})",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Cliente cadastrado com sucesso!', 'success')
            return redirect(url_for('clientes_pesquisar', submitted=1))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao cadastrar cliente. Tente novamente.', 'danger')
    
    return render_template('cliente_inserir.html', form=form)

@app.route('/cadastro/cliente/visualizar/<int:cliente_id>')
@login_required
@permission_required('pode_cadastrar_cliente')
def cliente_visualizar(cliente_id):
    """
    Rota para visualizar detalhes de um cliente.
    """
    cliente = Usuario.query.get_or_404(cliente_id)
    if cliente.tipo_usuario != 'restrito':
        abort(404)
    return render_template('cliente_visualizar.html', cliente=cliente)

@app.route('/cadastro/clientes/editar/<int:cliente_id>', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_cliente')
def clientes_editar(cliente_id):
    cliente = Usuario.query.get_or_404(cliente_id)
    if not (cliente.tipo_usuario == 'restrito' and cliente.perfil_funcionario is None):
        flash('Registro não é um cliente válido.', 'danger')
        return redirect(url_for('clientes_pesquisar', search=1))
    form = UsuarioEditForm(obj=cliente)
    if form.validate_on_submit():
        # Email não pode ser alterado
        cliente.nome = form.nome.data
        cliente.telefone = form.telefone.data
        cliente.ativo = form.ativo.data
        db.session.commit()
        flash('Cliente atualizado com sucesso!', 'success')
        return redirect(url_for('clientes_pesquisar', search=1))
    return render_template('cliente_form.html', form=form, cliente=cliente)

@app.route('/cadastro/clientes/excluir/<int:cliente_id>', methods=['POST'])
@login_required
@permission_required('pode_cadastrar_cliente')
def clientes_excluir(cliente_id):
    cliente = Usuario.query.get_or_404(cliente_id)
    if cliente.is_master() or cliente.perfil_funcionario is not None:
        flash('Não é permitido excluir este usuário.', 'danger')
        return redirect(url_for('clientes_pesquisar', search=1))
    db.session.delete(cliente)
    db.session.commit()
    flash('Cliente excluído com sucesso!', 'info')
    return redirect(url_for('clientes_pesquisar', search=1))

@app.route('/cadastro/funcionarios/pesquisar', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_funcionario')
def funcionarios_pesquisar():
    """Pesquisa/lista funcionários no padrão de serviços."""
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    show_results = request.args.get('search') == '1'
    field = request.args.get('field', 'nome')

    base_query = Funcionario.query.join(Usuario).join(Cargo)
    if query:
        if field == 'codigo' and query.isdigit():
            base_query = base_query.filter(Funcionario.id == int(query))
        elif field == 'email':
            base_query = base_query.filter(Usuario.email.ilike(f'%{query}%'))
        elif field == 'cargo':
            base_query = base_query.filter(Cargo.nome.ilike(f'%{query}%'))
        else:
            base_query = base_query.filter(Usuario.nome.ilike(f'%{query}%'))

    funcionarios = base_query.order_by(Usuario.nome).paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    form = FuncionarioForm()
    return render_template('funcionarios_pesquisa.html', funcionarios=funcionarios, form=form, query=query, per_page=per_page, show_results=show_results, field=field)


@app.route('/cadastro/usuarios/editar/<int:usuario_id>', methods=['GET', 'POST'])
@login_required
@master_required
def usuarios_editar(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    form = UsuarioEditForm(obj=usuario)
    if form.validate_on_submit():
        # Email não pode ser alterado
        usuario.nome = form.nome.data
        usuario.telefone = form.telefone.data
        usuario.ativo = form.ativo.data
        usuario.pode_cadastrar_cliente = form.pode_cadastrar_cliente.data
        usuario.pode_cadastrar_funcionario = form.pode_cadastrar_funcionario.data
        usuario.pode_cadastrar_cargo = form.pode_cadastrar_cargo.data
        usuario.pode_agendar = form.pode_agendar.data
        usuario.pode_ver_agendamentos = form.pode_ver_agendamentos.data
        usuario.pode_ver_relatorios = form.pode_ver_relatorios.data
        db.session.commit()
        flash('Usuário atualizado com sucesso!', 'success')
        return redirect(url_for('usuarios_pesquisar', search=1))
    return render_template('usuario_form.html', form=form, usuario=usuario)

@app.route('/cadastro/usuarios/excluir/<int:usuario_id>', methods=['POST'])
@login_required
@master_required
def usuarios_excluir(usuario_id):
    usuario = Usuario.query.get_or_404(usuario_id)
    if usuario.is_master():
        flash('Não é permitido excluir o usuário MASTER.', 'danger')
        return redirect(url_for('usuarios_pesquisar', search=1))
    db.session.delete(usuario)
    db.session.commit()
    flash('Usuário excluído com sucesso!', 'info')
    return redirect(url_for('usuarios_pesquisar', search=1))

@app.route('/cadastro/cliente', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_cliente')
def cadastro_cliente():
    """
    Rota para cadastro de novos clientes.
    """
    form = CadastroClienteForm()
    if form.validate_on_submit():
        if Usuario.query.filter_by(username=form.username.data).first():
            flash('Nome de usuário já existe.', 'danger')
            return render_template('cadastro.html', form=form, tipo='cliente')
        
        if Usuario.query.filter_by(email=form.email.data).first():
            flash('Email já cadastrado.', 'danger')
            return render_template('cadastro.html', form=form, tipo='cliente')
        
        usuario = Usuario(
            username=form.username.data,
            email=form.email.data,
            nome=form.nome.data,
            telefone=form.telefone.data,
            tipo_usuario='restrito'
        )
        usuario.set_password(form.password.data)
        
        db.session.add(usuario)
        db.session.commit()
        
        flash('Cliente cadastrado com sucesso!', 'success')
        return redirect(url_for('cadastro'))
    
    return render_template('cadastro.html', form=form, tipo='cliente')

@app.route('/funcionarios')
@login_required
@permission_required('pode_cadastrar_funcionario')
def funcionarios():
    """
    Rota principal de funcionários. Redireciona para a tela de pesquisa.
    """
    return redirect(url_for('funcionarios_pesquisar'))

@app.route('/funcionarios/criar', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_funcionario')
def criar_funcionario():
    """
    Rota para criar um novo funcionário.
    """
    form = FuncionarioForm()
    if form.validate_on_submit():
        funcionario_existente = Funcionario.query.filter_by(usuario_id=form.usuario_id.data).first()
        if funcionario_existente:
            flash('Usuário já é funcionário.', 'danger')
            return render_template('funcionario_inserir.html', form=form)
        
        funcionario = Funcionario(
            usuario_id=form.usuario_id.data,
            cargo_id=form.cargo_id.data,
            ativo=True
        )
        
        db.session.add(funcionario)
        db.session.commit()
        
        flash('Funcionário criado com sucesso!', 'success')
        return redirect(url_for('funcionarios_pesquisar', search=1))
    
    return render_template('funcionario_inserir.html', form=form)

@app.route('/cadastro/funcionario/visualizar/<int:funcionario_id>')
@login_required
@permission_required('pode_cadastrar_funcionario')
def funcionario_visualizar(funcionario_id):
    """
    Rota para visualizar detalhes de um funcionário.
    """
    funcionario = Funcionario.query.get_or_404(funcionario_id)
    return render_template('funcionario_visualizar.html', funcionario=funcionario)

@app.route('/cadastro/funcionario/editar/<int:funcionario_id>', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_funcionario')
def funcionario_editar(funcionario_id):
    """
    Rota para editar um funcionário existente.
    """
    funcionario = Funcionario.query.get_or_404(funcionario_id)
    form = FuncionarioForm(obj=funcionario)
    
    if form.validate_on_submit():
        funcionario.usuario_id = form.usuario_id.data
        funcionario.cargo_id = form.cargo_id.data
        
        db.session.commit()
        flash('Funcionário atualizado com sucesso!', 'success')
        return redirect(url_for('funcionarios_pesquisar', search=1))
    
    return render_template('funcionario_editar.html', form=form, funcionario=funcionario)

# --------------------------------------------------------------------------------------------------
# ROTAS DE CARGOS CORRIGIDAS E COMPLETAS
# --------------------------------------------------------------------------------------------------

@app.route('/cargos')
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_main():
    """
    Rota principal de cargos, redireciona para a página de pesquisa.
    """
    return redirect(url_for('cargos_pesquisar'))

@app.route('/cargos/pesquisar')
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_pesquisar():
    """
    Rota para pesquisar e exibir cargos com paginação.
    """
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    show_results = request.args.get('search') == '1'

    base_query = Cargo.query.order_by(Cargo.nome)
    field = request.args.get('field', 'nome')
    if query:
        if field == 'codigo' and query.isdigit():
            base_query = base_query.filter(Cargo.id == int(query))
        elif field == 'descricao':
            base_query = base_query.filter(Cargo.descricao.ilike(f'%{query}%'))
        else:
            base_query = base_query.filter(Cargo.nome.ilike(f'%{query}%'))

    cargos = base_query.paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    form = CargoForm()
    return render_template('cargos.html', cargos=cargos, form=form, query=query, per_page=per_page, show_results=show_results, field=field)

@app.route('/cargos/inserir/form', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_inserir_form():
    """
    Rota para exibir o formulário de inserção de cargo.
    """
    form = CargoForm()
    return render_template('cargo_form.html', form=form, titulo="Novo Cargo", action=url_for('cargos_inserir'))

@app.route('/cargos/inserir', methods=['POST'])
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_inserir():
    """
    Rota para processar a inserção de um novo cargo.
    """
    form = CargoForm()
    
    # Validações customizadas
    validation_errors = []
    
    if form.validate_on_submit():
        # Validar unicidade do nome
        if not validate_unique_cargo_name(form.nome.data):
            validation_errors.append('Já existe um cargo com este nome.')
        
        # Validar comprimento mínimo do nome
        if len(form.nome.data.strip()) < 2:
            validation_errors.append('Nome do cargo deve ter pelo menos 2 caracteres.')
        
        # Se há erros de validação, retornar com erros
        if validation_errors:
            for error in validation_errors:
                flash(error, 'danger')
            return render_template('cargo_form.html', form=form, titulo="Novo Cargo", action=url_for('cargos_inserir'), validation_errors=validation_errors)
        
        try:
            novo_cargo = Cargo(
                nome=form.nome.data.strip(),
                descricao=form.descricao.data.strip() if form.descricao.data else None
            )
            
            db.session.add(novo_cargo)
            db.session.commit()
            
            flash(f'Cargo "{novo_cargo.nome}" criado com sucesso!', 'success')
            return redirect(url_for('cargos_pesquisar'))
            
        except Exception as e:
            db.session.rollback()
            flash('Erro interno ao salvar o cargo. Tente novamente.', 'danger')
            current_app.logger.error(f"Erro ao criar cargo: {str(e)}")
    
    # Se chegou aqui, há erros de formulário
    if form.errors:
        validation_errors.extend(format_validation_errors(form.errors))
    
    return render_template('cargo_form.html', form=form, titulo="Novo Cargo", action=url_for('cargos_inserir'), validation_errors=validation_errors)

@app.route('/cargos/editar/<int:cargo_id>', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_editar(cargo_id):
    """
    Rota para editar um cargo existente.
    """
    cargo = Cargo.query.get_or_404(cargo_id)
    form = CargoForm(obj=cargo)
    
    if request.method == 'POST':
        validation_errors = []
        
        if form.validate_on_submit():
            # Validar unicidade do nome (excluindo o cargo atual)
            if not validate_unique_cargo_name(form.nome.data, exclude_cargo_id=cargo_id):
                validation_errors.append('Já existe outro cargo com este nome.')
            
            # Validar comprimento mínimo do nome
            if len(form.nome.data.strip()) < 2:
                validation_errors.append('Nome do cargo deve ter pelo menos 2 caracteres.')
            
            # Se há erros de validação, retornar com erros
            if validation_errors:
                for error in validation_errors:
                    flash(error, 'danger')
                return render_template('cargo_form.html', form=form, cargo=cargo, titulo="Editar Cargo", 
                                     action=url_for('cargos_editar', cargo_id=cargo.id), validation_errors=validation_errors)
            
            try:
                cargo.nome = form.nome.data.strip()
                cargo.descricao = form.descricao.data.strip() if form.descricao.data else None
                db.session.commit()
                
                flash(f'Cargo "{cargo.nome}" atualizado com sucesso!', 'success')
                return redirect(url_for('cargos_pesquisar'))
                
            except Exception as e:
                db.session.rollback()
                flash('Erro interno ao atualizar o cargo. Tente novamente.', 'danger')
                current_app.logger.error(f"Erro ao atualizar cargo: {str(e)}")
        
        # Se chegou aqui, há erros de formulário
        if form.errors:
            validation_errors.extend(format_validation_errors(form.errors))
            return render_template('cargo_form.html', form=form, cargo=cargo, titulo="Editar Cargo", 
                                 action=url_for('cargos_editar', cargo_id=cargo.id), validation_errors=validation_errors)
    
    return render_template('cargo_form.html', form=form, cargo=cargo, titulo="Editar Cargo", action=url_for('cargos_editar', cargo_id=cargo.id))

@app.route('/cargos/excluir/<int:cargo_id>', methods=['POST'])
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_excluir(cargo_id):
    """
    Rota para excluir um cargo, com verificação de integridade referencial.
    """
    cargo = Cargo.query.get_or_404(cargo_id)
    
    # Verificar integridade referencial
    reference_check = check_cargo_references(cargo_id)
    
    if not reference_check['can_delete']:
        referencias = reference_check['references']
        mensagens = []
        
        if referencias['funcionarios'] > 0:
            mensagens.append(f"{referencias['funcionarios']} funcionário(s)")
        
        flash(f'Não é possível excluir o cargo "{cargo.nome}" pois está sendo usado por: {", ".join(mensagens)}.', 'danger')
        return redirect(url_for('cargos_pesquisar'))
    
    try:
        cargo_nome = cargo.nome
        db.session.delete(cargo)
        db.session.commit()
        
        flash(f'Cargo "{cargo_nome}" excluído com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash('Erro interno ao excluir o cargo. Tente novamente.', 'danger')
        current_app.logger.error(f"Erro ao excluir cargo: {str(e)}")
    
    return redirect(url_for('cargos_pesquisar'))

@app.route('/cargos/check-references/<int:cargo_id>')
@login_required
@permission_required('pode_cadastrar_cargo')
def cargos_check_references(cargo_id):
    """
    API para verificar referências de um cargo antes da exclusão.
    """
    cargo = Cargo.query.get_or_404(cargo_id)
    reference_check = check_cargo_references(cargo_id)
    
    return jsonify({
        'cargo': {
            'id': cargo.id,
            'nome': cargo.nome
        },
        'can_delete': reference_check['can_delete'],
        'references': reference_check['references'],
        'total_references': reference_check['total_references']
    })

# --------------------------------------------------------------------------------------------------
# FIM DAS ROTAS DE CARGOS
# --------------------------------------------------------------------------------------------------

@app.route('/cadastro/servicos')
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_main():
    """Redireciona para a tela de pesquisa de serviços."""
    return redirect(url_for('servicos_pesquisar'))

@app.route('/cadastro/servicos/pesquisar', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_pesquisar():
    """Rota para pesquisar e exibir serviços com paginação, filtros e ordenação.

    Suporta resposta JSON quando format=json.
    """
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    format_json = request.args.get('format') == 'json'
    show_results = request.args.get('search') == '1'

    # Tamanho da página configurável (opções seguras)
    allowed_page_sizes = {5, 10, 20, 50}
    try:
        per_page = int(request.args.get('per_page', 10))
    except (TypeError, ValueError):
        per_page = 10
    if per_page not in allowed_page_sizes:
        per_page = 10

    # Filtros adicionais
    only_active_raw = request.args.get('only_active', '').lower()
    only_active = only_active_raw in {'1', 'true', 'on', 'yes'}

    def parse_float(name):
        value = request.args.get(name)
        if value is None or str(value).strip() == '':
            return None
        try:
            return float(str(value).replace(',', '.'))
        except ValueError:
            return None

    min_preco = parse_float('min_preco')
    max_preco = parse_float('max_preco')

    # Ordenação
    sort = request.args.get('sort', 'nome')
    direction = request.args.get('direction', 'asc')
    sort_map = {
        'nome': Servico.nome,
        'preco': Servico.preco,
        'duracao': Servico.duracao_minutos,
    }
    sort_column = sort_map.get(sort, Servico.nome)
    if direction == 'desc':
        sort_column = sort_column.desc()

    servicos = None

    if show_results or format_json:
        base_query = Servico.query

        if query:
            field = request.args.get('field', 'nome')
            if field == 'codigo' and query.isdigit():
                base_query = base_query.filter(Servico.id == int(query))
            else:
                base_query = base_query.filter(Servico.nome.ilike(f'%{query}%'))
        if only_active:
            base_query = base_query.filter(Servico.ativo.is_(True))
        if min_preco is not None:
            base_query = base_query.filter(Servico.preco >= min_preco)
        if max_preco is not None:
            base_query = base_query.filter(Servico.preco <= max_preco)

        base_query = base_query.order_by(sort_column)
        servicos = base_query.paginate(page=page, per_page=per_page, error_out=False)

    # Suporte a JSON para consumo via JS (sempre retorna resultados)
    if format_json:
        return jsonify({
            'items': [
                {
                    'id': s.id,
                    'nome': s.nome,
                    'descricao': s.descricao,
                    'preco': s.preco,
                    'duracao_minutos': s.duracao_minutos,
                    'ativo': s.ativo,
                }
                for s in (servicos.items if servicos else [])
            ],
            'pagination': {
                'page': servicos.page if servicos else 1,
                'per_page': per_page,
                'pages': servicos.pages if servicos else 0,
                'total': servicos.total if servicos else 0,
                'has_prev': servicos.has_prev if servicos else False,
                'has_next': servicos.has_next if servicos else False,
            }
        })

    form = ServicoForm()
    return render_template(
        'pesquisar_servico.html',
        servicos=servicos,
        form=form,
        show_results=show_results,
        # Filtros e estado da UI
        query=query,
        field=request.args.get('field', 'nome'),
        only_active=only_active,
        min_preco=min_preco,
        max_preco=max_preco,
        sort=sort,
        direction=direction,
        per_page=per_page,
    )

@app.route('/cadastro/servicos/inserir', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_inserir():
    """Rota para inserir um novo serviço."""
    form = ServicoForm()
    if form.validate_on_submit():
        servico_existente = Servico.query.filter_by(nome=form.nome.data).first()
        if servico_existente:
            flash('Já existe um serviço com este nome.', 'danger')
            return render_template('servico_inserir.html', form=form)

        novo_servico = Servico(
            nome=form.nome.data,
            descricao=form.descricao.data,
            preco=form.preco.data,
            duracao_minutos=form.duracao_minutos.data,
            ativo=form.ativo.data if hasattr(form, 'ativo') else True
        )
        db.session.add(novo_servico)
        db.session.commit()
        flash('Serviço adicionado com sucesso!', 'success')
        return redirect(url_for('servicos_pesquisar'))
    
    return render_template('servico_inserir.html', form=form)

@app.route('/cadastro/servicos/excluir/<int:servico_id>', methods=['POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_excluir(servico_id):
    """Deleta um serviço específico."""
    servico = Servico.query.get_or_404(servico_id)
    agendamentos_usando_servico = Agendamento.query.filter_by(servico_id=servico.id).first()

    if agendamentos_usando_servico:
        flash('Não é possível deletar este serviço, pois ele está associado a agendamentos existentes.', 'danger')
        return redirect(url_for('servicos_pesquisar'))

    db.session.delete(servico)
    db.session.commit()
    flash('Serviço deletado com sucesso!', 'info')
    return redirect(url_for('servicos_pesquisar'))

@app.route('/cadastro/servicos/visualizar/<int:servico_id>', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_visualizar(servico_id):
    """Exibe detalhes de um serviço."""
    servico = Servico.query.get_or_404(servico_id)
    return render_template('servico_detalhe.html', servico=servico)

@app.route('/cadastro/servicos/editar/<int:servico_id>', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def servicos_editar(servico_id):
    """Edita um serviço existente."""
    servico = Servico.query.get_or_404(servico_id)
    form = ServicoForm(obj=servico)
    if form.validate_on_submit():
        # Valores antigos para log de auditoria
        valores_antigos = {
            'nome': servico.nome,
            'preco': servico.preco,
            'ativo': servico.ativo
        }
        
        # Atualizar campos
        servico.nome = form.nome.data
        servico.descricao = form.descricao.data
        servico.categoria_id = form.categoria_id.data if form.categoria_id.data else None
        servico.preco = form.preco.data
        servico.custo = form.custo.data
        servico.percentual_comissao = form.percentual_comissao.data
        servico.duracao_minutos = form.duracao_minutos.data
        servico.intervalo_entre_agendamentos = form.intervalo_entre_agendamentos.data
        servico.max_agendamentos_dia = form.max_agendamentos_dia.data
        servico.antecedencia_minima_horas = form.antecedencia_minima_horas.data
        servico.preco_promocional = form.preco_promocional.data
        servico.data_inicio_promocao = form.data_inicio_promocao.data
        servico.data_fim_promocao = form.data_fim_promocao.data
        servico.ordem = form.ordem.data
        servico.ativo = form.ativo.data
        
        try:
            db.session.commit()
            
            # Log de auditoria
            log = LogAuditoria(
                usuario_id=current_user.id,
                acao='UPDATE',
                tabela='servicos',
                registro_id=servico.id,
                valores_antigos=str(valores_antigos),
                valores_novos=f"Serviço: {servico.nome} - R$ {servico.preco}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Serviço atualizado com sucesso!', 'success')
            return redirect(url_for('servicos_pesquisar'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar serviço. Tente novamente.', 'danger')
    
    return render_template('servico_form.html', form=form, servico=servico)

# ========================================
# ROTAS PARA CATEGORIAS DE SERVIÇOS
# ========================================

@app.route('/cadastro/categorias-servico')
@login_required
@permission_required('pode_cadastrar_servico')
def categorias_servico_main():
    """Redireciona para a tela de pesquisa de categorias."""
    return redirect(url_for('categorias_servico_pesquisar'))

@app.route('/cadastro/categorias-servico/pesquisar', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_servico')
def categorias_servico_pesquisar():
    """Pesquisa e lista categorias de serviços."""
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    show_results = request.args.get('search') == '1'
    
    base_query = CategoriaServico.query.order_by(CategoriaServico.ordem, CategoriaServico.nome)
    
    if query:
        base_query = base_query.filter(CategoriaServico.nome.ilike(f'%{query}%'))
    
    categorias = base_query.paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    form = CategoriaServicoForm()
    
    return render_template('categorias_servico_pesquisa.html', 
                         categorias=categorias, form=form, query=query, 
                         per_page=per_page, show_results=show_results)

@app.route('/cadastro/categorias-servico/inserir', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def categorias_servico_inserir():
    """Insere uma nova categoria de serviço."""
    form = CategoriaServicoForm()
    if form.validate_on_submit():
        if CategoriaServico.query.filter_by(nome=form.nome.data).first():
            flash('Já existe uma categoria com este nome.', 'danger')
            return render_template('categoria_servico_inserir.html', form=form)
        
        categoria = CategoriaServico(
            nome=form.nome.data,
            descricao=form.descricao.data,
            cor=form.cor.data,
            ordem=form.ordem.data,
            ativo=form.ativo.data
        )
        
        try:
            db.session.add(categoria)
            db.session.commit()
            
            # Log de auditoria
            log = LogAuditoria(
                usuario_id=current_user.id,
                acao='CREATE',
                tabela='categorias_servico',
                registro_id=categoria.id,
                valores_novos=f"Categoria: {categoria.nome}",
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            flash('Categoria criada com sucesso!', 'success')
            return redirect(url_for('categorias_servico_pesquisar', search=1))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar categoria. Tente novamente.', 'danger')
    
    return render_template('categoria_servico_inserir.html', form=form)

@app.route('/cadastro/categorias-servico/editar/<int:categoria_id>', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def categorias_servico_editar(categoria_id):
    """Edita uma categoria de serviço."""
    categoria = CategoriaServico.query.get_or_404(categoria_id)
    form = CategoriaServicoForm(obj=categoria)
    
    if form.validate_on_submit():
        categoria.nome = form.nome.data
        categoria.descricao = form.descricao.data
        categoria.cor = form.cor.data
        categoria.ordem = form.ordem.data
        categoria.ativo = form.ativo.data
        
        try:
            db.session.commit()
            flash('Categoria atualizada com sucesso!', 'success')
            return redirect(url_for('categorias_servico_pesquisar', search=1))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar categoria. Tente novamente.', 'danger')
    
    return render_template('categoria_servico_form.html', form=form, categoria=categoria)

@app.route('/cadastro/categorias-servico/excluir/<int:categoria_id>', methods=['POST'])
@login_required
@permission_required('pode_cadastrar_servico')
def categorias_servico_excluir(categoria_id):
    """Exclui uma categoria de serviço."""
    categoria = CategoriaServico.query.get_or_404(categoria_id)
    
    # Verificar se há serviços usando esta categoria
    servicos_usando = Servico.query.filter_by(categoria_id=categoria_id).count()
    if servicos_usando > 0:
        flash(f'Não é possível excluir esta categoria. Existem {servicos_usando} serviços associados.', 'danger')
        return redirect(url_for('categorias_servico_pesquisar', search=1))
    
    try:
        db.session.delete(categoria)
        db.session.commit()
        flash('Categoria excluída com sucesso!', 'info')
    except Exception as e:
        db.session.rollback()
        flash('Erro ao excluir categoria. Tente novamente.', 'danger')
    
    return redirect(url_for('categorias_servico_pesquisar', search=1))

# ========================================
# ROTAS PARA ESPECIALIDADES DE FUNCIONÁRIOS
# ========================================

@app.route('/cadastro/especialidades')
@login_required
@permission_required('pode_cadastrar_funcionario')
def especialidades_main():
    """Redireciona para a tela de pesquisa de especialidades."""
    return redirect(url_for('especialidades_pesquisar'))

@app.route('/cadastro/especialidades/pesquisar', methods=['GET'])
@login_required
@permission_required('pode_cadastrar_funcionario')
def especialidades_pesquisar():
    """Pesquisa e lista especialidades de funcionários."""
    query = request.args.get('query', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = int(request.args.get('per_page', 10)) if str(request.args.get('per_page', '10')).isdigit() else 10
    show_results = request.args.get('search') == '1'
    
    base_query = EspecialidadeFuncionario.query.order_by(EspecialidadeFuncionario.nome)
    
    if query:
        base_query = base_query.filter(EspecialidadeFuncionario.nome.ilike(f'%{query}%'))
    
    especialidades = base_query.paginate(page=page, per_page=per_page, error_out=False) if show_results else None
    form = EspecialidadeFuncionarioForm()
    
    return render_template('especialidades_pesquisa.html', 
                         especialidades=especialidades, form=form, query=query, 
                         per_page=per_page, show_results=show_results)

@app.route('/cadastro/especialidades/inserir', methods=['GET', 'POST'])
@login_required
@permission_required('pode_cadastrar_funcionario')
def especialidades_inserir():
    """Insere uma nova especialidade."""
    form = EspecialidadeFuncionarioForm()
    if form.validate_on_submit():
        if EspecialidadeFuncionario.query.filter_by(nome=form.nome.data).first():
            flash('Já existe uma especialidade com este nome.', 'danger')
            return render_template('especialidade_inserir.html', form=form)
        
        especialidade = EspecialidadeFuncionario(
            nome=form.nome.data,
            descricao=form.descricao.data,
            ativo=form.ativo.data
        )
        
        try:
            db.session.add(especialidade)
            db.session.commit()
            flash('Especialidade criada com sucesso!', 'success')
            return redirect(url_for('especialidades_pesquisar', search=1))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao criar especialidade. Tente novamente.', 'danger')
    
    return render_template('especialidade_inserir.html', form=form)

# ========================================
# ROTAS PARA RELATÓRIOS AVANÇADOS
# ========================================

@app.route('/relatorios/cadastros')
@login_required
@permission_required('pode_ver_relatorios')
def relatorios_cadastros():
    """Dashboard de relatórios de cadastros."""
    
    # Estatísticas gerais
    total_usuarios = Usuario.query.count()
    total_clientes = Usuario.query.filter(
        Usuario.tipo_usuario == 'restrito',
        Usuario.perfil_funcionario == None
    ).count()
    total_funcionarios = Funcionario.query.filter_by(ativo=True).count()
    total_servicos = Servico.query.filter_by(ativo=True).count()
    total_cargos = Cargo.query.filter_by(ativo=True).count()
    
    # Crescimento mensal de clientes (últimos 6 meses)
    hoje = datetime.now().date()
    crescimento_clientes = []
    for i in range(5, -1, -1):
        data_inicio = (hoje.replace(day=1) - timedelta(days=32*i)).replace(day=1)
        data_fim = (data_inicio.replace(month=data_inicio.month % 12 + 1) if data_inicio.month < 12 
                   else data_inicio.replace(year=data_inicio.year + 1, month=1)) - timedelta(days=1)
        
        novos_clientes = Usuario.query.filter(
            Usuario.tipo_usuario == 'restrito',
            Usuario.perfil_funcionario == None,
            Usuario.criado_em >= data_inicio,
            Usuario.criado_em <= data_fim
        ).count()
        
        crescimento_clientes.append({
            'mes': data_inicio.strftime('%b/%Y'),
            'total': novos_clientes
        })
    
    # Top 5 serviços mais procurados
    top_servicos = db.session.query(
        Servico.nome,
        func.count(Agendamento.id).label('total_agendamentos')
    ).join(Agendamento).group_by(Servico.id).order_by(
        func.count(Agendamento.id).desc()
    ).limit(5).all()
    
    # Funcionários por cargo
    funcionarios_por_cargo = db.session.query(
        Cargo.nome,
        func.count(Funcionario.id).label('total')
    ).join(Funcionario).filter(Funcionario.ativo == True).group_by(Cargo.id).all()
    
    # Clientes por estado
    clientes_por_estado = db.session.query(
        Usuario.estado,
        func.count(Usuario.id).label('total')
    ).filter(
        Usuario.tipo_usuario == 'restrito',
        Usuario.perfil_funcionario == None,
        Usuario.estado.isnot(None)
    ).group_by(Usuario.estado).order_by(func.count(Usuario.id).desc()).limit(10).all()
    
    # Logs de auditoria recentes (últimas 50 ações)
    logs_recentes = LogAuditoria.query.order_by(LogAuditoria.timestamp.desc()).limit(50).all()
    
    return render_template('relatorios_cadastros.html',
                         stats={
                             'total_usuarios': total_usuarios,
                             'total_clientes': total_clientes,
                             'total_funcionarios': total_funcionarios,
                             'total_servicos': total_servicos,
                             'total_cargos': total_cargos
                         },
                         crescimento_clientes=crescimento_clientes,
                         top_servicos=top_servicos,
                         funcionarios_por_cargo=funcionarios_por_cargo,
                         clientes_por_estado=clientes_por_estado,
                         logs_recentes=logs_recentes)

@app.route('/relatorios/clientes')
@login_required
@permission_required('pode_ver_relatorios')
def relatorio_clientes():
    """Relatório detalhado de clientes."""
    
    # Filtros
    estado = request.args.get('estado', '')
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    # Query base
    query = Usuario.query.filter(
        Usuario.tipo_usuario == 'restrito',
        Usuario.perfil_funcionario == None
    )
    
    # Aplicar filtros
    if estado:
        query = query.filter(Usuario.estado == estado)
    
    if data_inicio:
        try:
            data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
            query = query.filter(Usuario.criado_em >= data_inicio_dt)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
            query = query.filter(Usuario.criado_em <= data_fim_dt)
        except ValueError:
            pass
    
    clientes = query.order_by(Usuario.criado_em.desc()).all()
    
    # Estatísticas dos clientes filtrados
    total_clientes = len(clientes)
    clientes_com_agendamentos = sum(1 for c in clientes if c.total_agendamentos > 0)
    
    # Estados para o filtro
    estados_disponiveis = db.session.query(Usuario.estado).filter(
        Usuario.tipo_usuario == 'restrito',
        Usuario.perfil_funcionario == None,
        Usuario.estado.isnot(None)
    ).distinct().order_by(Usuario.estado).all()
    
    return render_template('relatorio_clientes.html',
                         clientes=clientes,
                         total_clientes=total_clientes,
                         clientes_com_agendamentos=clientes_com_agendamentos,
                         estados_disponiveis=[e[0] for e in estados_disponiveis],
                         filtros={
                             'estado': estado,
                             'data_inicio': data_inicio,
                             'data_fim': data_fim
                         })

@app.route('/relatorios/funcionarios')
@login_required
@permission_required('pode_ver_relatorios')
def relatorio_funcionarios():
    """Relatório detalhado de funcionários."""
    
    # Filtros
    cargo_id = request.args.get('cargo_id', type=int)
    apenas_ativos = request.args.get('apenas_ativos', 'true') == 'true'
    
    # Query base
    query = Funcionario.query.join(Usuario).join(Cargo)
    
    # Aplicar filtros
    if cargo_id:
        query = query.filter(Funcionario.cargo_id == cargo_id)
    
    if apenas_ativos:
        query = query.filter(Funcionario.ativo == True)
    
    funcionarios = query.order_by(Usuario.nome).all()
    
    # Calcular estatísticas
    for funcionario in funcionarios:
        funcionario.atualizar_estatisticas()
    
    # Cargos para o filtro
    cargos_disponiveis = Cargo.query.filter_by(ativo=True).order_by(Cargo.nome).all()
    
    return render_template('relatorio_funcionarios.html',
                         funcionarios=funcionarios,
                         cargos_disponiveis=cargos_disponiveis,
                         filtros={
                             'cargo_id': cargo_id,
                             'apenas_ativos': apenas_ativos
                         })

@app.route('/relatorios/servicos')
@login_required
@permission_required('pode_ver_relatorios')
def relatorio_servicos():
    """Relatório detalhado de serviços."""
    
    # Filtros
    categoria_id = request.args.get('categoria_id', type=int)
    apenas_ativos = request.args.get('apenas_ativos', 'true') == 'true'
    ordenar_por = request.args.get('ordenar_por', 'popularidade')
    
    # Query base
    query = Servico.query
    
    # Aplicar filtros
    if categoria_id:
        query = query.filter(Servico.categoria_id == categoria_id)
    
    if apenas_ativos:
        query = query.filter(Servico.ativo == True)
    
    # Ordenação
    if ordenar_por == 'popularidade':
        query = query.order_by(Servico.total_agendamentos.desc())
    elif ordenar_por == 'preco':
        query = query.order_by(Servico.preco.desc())
    elif ordenar_por == 'margem':
        # Ordenar por margem de lucro (calculada dinamicamente)
        query = query.order_by((Servico.preco - Servico.custo).desc())
    else:
        query = query.order_by(Servico.nome)
    
    servicos = query.all()
    
    # Atualizar estatísticas
    for servico in servicos:
        servico.atualizar_estatisticas()
    
    # Categorias para o filtro
    categorias_disponiveis = CategoriaServico.query.filter_by(ativo=True).order_by(CategoriaServico.nome).all()
    
    # Estatísticas gerais
    receita_total = sum(s.preco * s.total_agendamentos for s in servicos)
    servico_mais_popular = max(servicos, key=lambda s: s.total_agendamentos) if servicos else None
    
    return render_template('relatorio_servicos.html',
                         servicos=servicos,
                         categorias_disponiveis=categorias_disponiveis,
                         receita_total=receita_total,
                         servico_mais_popular=servico_mais_popular,
                         filtros={
                             'categoria_id': categoria_id,
                             'apenas_ativos': apenas_ativos,
                             'ordenar_por': ordenar_por
                         })

@app.route('/api/relatorios/dashboard-data')
@login_required
@permission_required('pode_ver_relatorios')
def api_dashboard_data():
    """API para dados do dashboard (para gráficos dinâmicos)."""
    
    tipo = request.args.get('tipo', 'geral')
    
    if tipo == 'crescimento_clientes':
        # Crescimento de clientes nos últimos 12 meses
        hoje = datetime.now().date()
        dados = []
        
        for i in range(11, -1, -1):
            data_inicio = (hoje.replace(day=1) - timedelta(days=32*i)).replace(day=1)
            data_fim = (data_inicio.replace(month=data_inicio.month % 12 + 1) if data_inicio.month < 12 
                       else data_inicio.replace(year=data_inicio.year + 1, month=1)) - timedelta(days=1)
            
            novos_clientes = Usuario.query.filter(
                Usuario.tipo_usuario == 'restrito',
                Usuario.perfil_funcionario == None,
                Usuario.criado_em >= data_inicio,
                Usuario.criado_em <= data_fim
            ).count()
            
            dados.append({
                'mes': data_inicio.strftime('%b/%Y'),
                'total': novos_clientes
            })
        
        return jsonify(dados)
    
    elif tipo == 'servicos_performance':
        # Performance dos serviços
        servicos = db.session.query(
            Servico.nome,
            Servico.preco,
            func.count(Agendamento.id).label('total_agendamentos'),
            func.sum(Agendamento.valor_final).label('receita_total')
        ).outerjoin(Agendamento).filter(Servico.ativo == True).group_by(Servico.id).all()
        
        dados = [
            {
                'nome': s.nome,
                'preco': float(s.preco),
                'agendamentos': s.total_agendamentos or 0,
                'receita': float(s.receita_total or 0)
            }
            for s in servicos
        ]
        
        return jsonify(dados)
    
    else:
        return jsonify({'error': 'Tipo de relatório não encontrado'}), 404

# ========================================
# ROTAS PARA BACKUP E RESTORE
# ========================================

@app.route('/admin/backup')
@login_required
@master_required
def backup_main():
    """Página principal de backup e restore."""
    return render_template('backup_restore.html')

@app.route('/admin/backup/gerar')
@login_required
@master_required
def gerar_backup():
    """Gera e download do backup completo do sistema."""
    
    try:
        # Criar um arquivo temporário para o backup
        backup_buffer = BytesIO()
        
        with zipfile.ZipFile(backup_buffer, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
            
            # Backup dos usuários
            usuarios_data = []
            for usuario in Usuario.query.all():
                usuarios_data.append({
                    'id': usuario.id,
                    'username': usuario.username,
                    'email': usuario.email,
                    'nome': usuario.nome,
                    'telefone': usuario.telefone,
                    'cpf_cnpj': usuario.cpf_cnpj,
                    'endereco': usuario.endereco,
                    'cidade': usuario.cidade,
                    'estado': usuario.estado,
                    'cep': usuario.cep,
                    'data_nascimento': usuario.data_nascimento.isoformat() if usuario.data_nascimento else None,
                    'observacoes': usuario.observacoes,
                    'tipo_usuario': usuario.tipo_usuario,
                    'ativo': usuario.ativo,
                    'criado_em': usuario.criado_em.isoformat() if usuario.criado_em else None,
                    'ultimo_login': usuario.ultimo_login.isoformat() if usuario.ultimo_login else None,
                    # Permissões
                    'pode_cadastrar_cliente': usuario.pode_cadastrar_cliente,
                    'pode_cadastrar_funcionario': usuario.pode_cadastrar_funcionario,
                    'pode_cadastrar_cargo': usuario.pode_cadastrar_cargo,
                    'pode_cadastrar_servico': usuario.pode_cadastrar_servico,
                    'pode_agendar': usuario.pode_agendar,
                    'pode_ver_agendamentos': usuario.pode_ver_agendamentos,
                    'pode_ver_relatorios': usuario.pode_ver_relatorios,
                    'pode_configurar_sistema': usuario.pode_configurar_sistema
                })
            
            backup_zip.writestr('usuarios.json', json.dumps(usuarios_data, indent=2, ensure_ascii=False))
            
            # Backup dos cargos
            cargos_data = []
            for cargo in Cargo.query.all():
                cargos_data.append({
                    'id': cargo.id,
                    'nome': cargo.nome,
                    'descricao': cargo.descricao,
                    'ativo': cargo.ativo,
                    'cargo_pai_id': cargo.cargo_pai_id,
                    'nivel_hierarquico': cargo.nivel_hierarquico,
                    'salario_base': cargo.salario_base,
                    'percentual_comissao': cargo.percentual_comissao,
                    'carga_horaria_semanal': cargo.carga_horaria_semanal,
                    'permissoes_json': cargo.permissoes_json,
                    'criado_em': cargo.criado_em.isoformat() if cargo.criado_em else None
                })
            
            backup_zip.writestr('cargos.json', json.dumps(cargos_data, indent=2, ensure_ascii=False))
            
            # Backup das categorias de serviço
            categorias_data = []
            for categoria in CategoriaServico.query.all():
                categorias_data.append({
                    'id': categoria.id,
                    'nome': categoria.nome,
                    'descricao': categoria.descricao,
                    'ativo': categoria.ativo,
                    'ordem': categoria.ordem,
                    'cor': categoria.cor,
                    'criado_em': categoria.criado_em.isoformat() if categoria.criado_em else None
                })
            
            backup_zip.writestr('categorias_servico.json', json.dumps(categorias_data, indent=2, ensure_ascii=False))
            
            # Backup dos serviços
            servicos_data = []
            for servico in Servico.query.all():
                servicos_data.append({
                    'id': servico.id,
                    'nome': servico.nome,
                    'descricao': servico.descricao,
                    'categoria_id': servico.categoria_id,
                    'preco': servico.preco,
                    'custo': servico.custo,
                    'percentual_comissao': servico.percentual_comissao,
                    'duracao_minutos': servico.duracao_minutos,
                    'intervalo_entre_agendamentos': servico.intervalo_entre_agendamentos,
                    'max_agendamentos_dia': servico.max_agendamentos_dia,
                    'antecedencia_minima_horas': servico.antecedencia_minima_horas,
                    'preco_promocional': servico.preco_promocional,
                    'data_inicio_promocao': servico.data_inicio_promocao.isoformat() if servico.data_inicio_promocao else None,
                    'data_fim_promocao': servico.data_fim_promocao.isoformat() if servico.data_fim_promocao else None,
                    'ordem': servico.ordem,
                    'ativo': servico.ativo,
                    'total_agendamentos': servico.total_agendamentos,
                    'avaliacao_media': servico.avaliacao_media,
                    'criado_em': servico.criado_em.isoformat() if servico.criado_em else None
                })
            
            backup_zip.writestr('servicos.json', json.dumps(servicos_data, indent=2, ensure_ascii=False))
            
            # Backup das especialidades
            especialidades_data = []
            for especialidade in EspecialidadeFuncionario.query.all():
                especialidades_data.append({
                    'id': especialidade.id,
                    'nome': especialidade.nome,
                    'descricao': especialidade.descricao,
                    'ativo': especialidade.ativo
                })
            
            backup_zip.writestr('especialidades.json', json.dumps(especialidades_data, indent=2, ensure_ascii=False))
            
            # Backup dos funcionários
            funcionarios_data = []
            for funcionario in Funcionario.query.all():
                funcionarios_data.append({
                    'id': funcionario.id,
                    'usuario_id': funcionario.usuario_id,
                    'cargo_id': funcionario.cargo_id,
                    'data_contratacao': funcionario.data_contratacao.isoformat() if funcionario.data_contratacao else None,
                    'ativo': funcionario.ativo,
                    'registro_profissional': funcionario.registro_profissional,
                    'observacoes': funcionario.observacoes,
                    'horario_inicio': funcionario.horario_inicio.isoformat() if funcionario.horario_inicio else None,
                    'horario_fim': funcionario.horario_fim.isoformat() if funcionario.horario_fim else None,
                    'trabalha_sabado': funcionario.trabalha_sabado,
                    'trabalha_domingo': funcionario.trabalha_domingo,
                    'tipo_comissao': funcionario.tipo_comissao,
                    'valor_comissao': funcionario.valor_comissao,
                    'total_agendamentos': funcionario.total_agendamentos,
                    'total_agendamentos_concluidos': funcionario.total_agendamentos_concluidos,
                    'avaliacao_media': funcionario.avaliacao_media,
                    'criado_em': funcionario.criado_em.isoformat() if funcionario.criado_em else None,
                    'especialidades': [e.id for e in funcionario.especialidades],
                    'servicos_habilitados': [s.id for s in funcionario.servicos_habilitados]
                })
            
            backup_zip.writestr('funcionarios.json', json.dumps(funcionarios_data, indent=2, ensure_ascii=False))
            
            # Backup dos agendamentos
            agendamentos_data = []
            for agendamento in Agendamento.query.all():
                agendamentos_data.append({
                    'id': agendamento.id,
                    'cliente_id': agendamento.cliente_id,
                    'funcionario_id': agendamento.funcionario_id,
                    'servico_id': agendamento.servico_id,
                    'data_agendamento': agendamento.data_agendamento.isoformat(),
                    'status': agendamento.status,
                    'observacoes': agendamento.observacoes,
                    'servico': agendamento.servico,  # Campo legado
                    'duracao_minutos': agendamento.duracao_minutos,
                    'preco_cobrado': agendamento.preco_cobrado,
                    'desconto_aplicado': agendamento.desconto_aplicado,
                    'valor_final': agendamento.valor_final,
                    'criado_em': agendamento.criado_em.isoformat() if agendamento.criado_em else None,
                    'atualizado_em': agendamento.atualizado_em.isoformat() if agendamento.atualizado_em else None,
                    'data_cancelamento': agendamento.data_cancelamento.isoformat() if agendamento.data_cancelamento else None,
                    'data_conclusao': agendamento.data_conclusao.isoformat() if agendamento.data_conclusao else None,
                    'avaliacao': agendamento.avaliacao,
                    'comentario_avaliacao': agendamento.comentario_avaliacao
                })
            
            backup_zip.writestr('agendamentos.json', json.dumps(agendamentos_data, indent=2, ensure_ascii=False))
            
            # Backup das configurações da empresa
            config_data = []
            for config in ConfiguracaoEmpresa.query.all():
                config_data.append({
                    'id': config.id,
                    'nome_empresa': config.nome_empresa,
                    'logo_path': config.logo_path,
                    'whatsapp_token': config.whatsapp_token,
                    'whatsapp_phone_id': config.whatsapp_phone_id,
                    'whatsapp_webhook_verify_token': config.whatsapp_webhook_verify_token,
                    'atualizado_em': config.atualizado_em.isoformat() if config.atualizado_em else None
                })
            
            backup_zip.writestr('configuracao_empresa.json', json.dumps(config_data, indent=2, ensure_ascii=False))
            
            # Backup dos logs de auditoria (últimos 1000 registros)
            logs_data = []
            for log in LogAuditoria.query.order_by(LogAuditoria.timestamp.desc()).limit(1000).all():
                logs_data.append({
                    'id': log.id,
                    'usuario_id': log.usuario_id,
                    'acao': log.acao,
                    'tabela': log.tabela,
                    'registro_id': log.registro_id,
                    'valores_antigos': log.valores_antigos,
                    'valores_novos': log.valores_novos,
                    'timestamp': log.timestamp.isoformat() if log.timestamp else None,
                    'ip_address': log.ip_address
                })
            
            backup_zip.writestr('logs_auditoria.json', json.dumps(logs_data, indent=2, ensure_ascii=False))
            
            # Metadados do backup
            metadata = {
                'versao': '1.0',
                'data_backup': datetime.utcnow().isoformat(),
                'usuario_backup': current_user.username,
                'total_registros': {
                    'usuarios': len(usuarios_data),
                    'cargos': len(cargos_data),
                    'categorias_servico': len(categorias_data),
                    'servicos': len(servicos_data),
                    'especialidades': len(especialidades_data),
                    'funcionarios': len(funcionarios_data),
                    'agendamentos': len(agendamentos_data),
                    'configuracao_empresa': len(config_data),
                    'logs_auditoria': len(logs_data)
                }
            }
            
            backup_zip.writestr('metadata.json', json.dumps(metadata, indent=2, ensure_ascii=False))
        
        backup_buffer.seek(0)
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=current_user.id,
            acao='BACKUP',
            tabela='sistema',
            valores_novos=f"Backup completo gerado - {metadata['total_registros']}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        # Preparar nome do arquivo
        data_atual = datetime.now().strftime('%Y%m%d_%H%M%S')
        nome_arquivo = f'backup_sistema_{data_atual}.zip'
        
        return send_file(
            backup_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=nome_arquivo
        )
        
    except Exception as e:
        flash(f'Erro ao gerar backup: {str(e)}', 'danger')
        return redirect(url_for('backup_main'))

@app.route('/admin/backup/exportar-csv/<string:tabela>')
@login_required
@master_required
def exportar_csv(tabela):
    """Exporta uma tabela específica em formato CSV."""
    
    try:
        output = BytesIO()
        
        if tabela == 'usuarios':
            # Exportar usuários/clientes
            usuarios = Usuario.query.filter(
                Usuario.tipo_usuario == 'restrito',
                Usuario.perfil_funcionario == None
            ).all()
            
            fieldnames = ['ID', 'Nome', 'Email', 'Telefone', 'CPF/CNPJ', 'Endereço', 
                         'Cidade', 'Estado', 'CEP', 'Data Nascimento', 'Data Cadastro', 
                         'Total Agendamentos', 'Ativo']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';', 
                                  quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writeheader()
            
            for usuario in usuarios:
                writer.writerow({
                    'ID': usuario.id,
                    'Nome': usuario.nome,
                    'Email': usuario.email,
                    'Telefone': usuario.telefone or '',
                    'CPF/CNPJ': usuario.cpf_cnpj or '',
                    'Endereço': usuario.endereco or '',
                    'Cidade': usuario.cidade or '',
                    'Estado': usuario.estado or '',
                    'CEP': usuario.cep or '',
                    'Data Nascimento': usuario.data_nascimento.strftime('%d/%m/%Y') if usuario.data_nascimento else '',
                    'Data Cadastro': usuario.criado_em.strftime('%d/%m/%Y %H:%M') if usuario.criado_em else '',
                    'Total Agendamentos': usuario.total_agendamentos,
                    'Ativo': 'Sim' if usuario.ativo else 'Não'
                })
            
            nome_arquivo = f'clientes_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif tabela == 'servicos':
            # Exportar serviços
            servicos = Servico.query.all()
            
            fieldnames = ['ID', 'Nome', 'Categoria', 'Preço', 'Duração (min)', 
                         'Total Agendamentos', 'Margem Lucro (%)', 'Ativo']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';', 
                                  quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writeheader()
            
            for servico in servicos:
                writer.writerow({
                    'ID': servico.id,
                    'Nome': servico.nome,
                    'Categoria': servico.categoria.nome if servico.categoria else '',
                    'Preço': f'R$ {servico.preco:.2f}',
                    'Duração (min)': servico.duracao_minutos,
                    'Total Agendamentos': servico.total_agendamentos,
                    'Margem Lucro (%)': f'{servico.margem_lucro:.1f}%',
                    'Ativo': 'Sim' if servico.ativo else 'Não'
                })
            
            nome_arquivo = f'servicos_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        elif tabela == 'funcionarios':
            # Exportar funcionários
            funcionarios = Funcionario.query.join(Usuario).join(Cargo).all()
            
            fieldnames = ['ID', 'Nome', 'Email', 'Cargo', 'Data Contratação', 
                         'Registro Profissional', 'Total Agendamentos', 'Taxa Conclusão (%)', 'Ativo']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=';', 
                                  quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writeheader()
            
            for funcionario in funcionarios:
                writer.writerow({
                    'ID': funcionario.id,
                    'Nome': funcionario.usuario.nome,
                    'Email': funcionario.usuario.email,
                    'Cargo': funcionario.cargo.nome,
                    'Data Contratação': funcionario.data_contratacao.strftime('%d/%m/%Y') if funcionario.data_contratacao else '',
                    'Registro Profissional': funcionario.registro_profissional or '',
                    'Total Agendamentos': funcionario.total_agendamentos,
                    'Taxa Conclusão (%)': f'{funcionario.taxa_conclusao:.1f}%',
                    'Ativo': 'Sim' if funcionario.ativo else 'Não'
                })
            
            nome_arquivo = f'funcionarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
        else:
            flash('Tabela não encontrada para exportação.', 'danger')
            return redirect(url_for('backup_main'))
        
        output.seek(0)
        
        # Log de auditoria
        log = LogAuditoria(
            usuario_id=current_user.id,
            acao='EXPORT_CSV',
            tabela=tabela,
            valores_novos=f"Exportação CSV de {tabela}",
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=nome_arquivo
        )
        
    except Exception as e:
        flash(f'Erro ao exportar CSV: {str(e)}', 'danger')
        return redirect(url_for('backup_main'))

@app.route('/agendamentos')
@login_required
@permission_required('pode_ver_agendamentos')
def agendamentos():
    """
    Exibe a lista de agendamentos com base nas permissões do usuário.
    """
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    if current_user.is_master():
        agendamentos = Agendamento.query.order_by(Agendamento.data_agendamento.desc())\
                                        .paginate(page=page, per_page=per_page, error_out=False)
    elif current_user.is_funcionario():
        funcionario = Funcionario.query.filter_by(usuario_id=current_user.id).first()
        if funcionario:
            agendamentos = Agendamento.query.filter_by(funcionario_id=funcionario.id)\
                                             .order_by(Agendamento.data_agendamento.desc())\
                                             .paginate(page=page, per_page=per_page, error_out=False)
        else:
            agendamentos = None
    else:
        agendamentos = Agendamento.query.filter_by(cliente_id=current_user.id)\
                                        .order_by(Agendamento.data_agendamento.desc())\
                                        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('agendamentos.html', agendamentos=agendamentos)

@app.route('/agendar', methods=['GET', 'POST'])
@login_required
@permission_required('pode_agendar')
def agendar():
    """
    Rota para criar um novo agendamento.
    A duração do agendamento é obtida dinamicamente do serviço selecionado.
    """
    form = AgendamentoForm()
    
    if form.validate_on_submit():
        servico_selecionado = Servico.query.get(form.servico_id.data)

        data_inicio = form.data_agendamento.data
        data_fim = data_inicio + timedelta(minutes=servico_selecionado.duracao_minutos)

        conflito = Agendamento.query.filter(
            and_(
                Agendamento.funcionario_id == form.funcionario_id.data,
                Agendamento.status == 'agendado',
                or_(
                    and_(Agendamento.data_agendamento < data_fim, Agendamento.data_fim > data_inicio),
                    and_(Agendamento.data_agendamento == data_inicio)
                )
            )
        ).first()
        
        if conflito:
            flash('Já existe um agendamento para este funcionário neste horário ou há um conflito de horários.', 'danger')
            return render_template('agendar.html', form=form)
        
        agendamento = Agendamento(
            cliente_id=form.cliente_id.data,
            funcionario_id=form.funcionario_id.data,
            data_agendamento=form.data_agendamento.data,
            servico_id=form.servico_id.data,
            duracao_minutos=servico_selecionado.duracao_minutos,
            preco_total=servico_selecionado.preco,
            observacoes=form.observacoes.data
        )
        
        db.session.add(agendamento)
        db.session.commit()
        
        flash('Agendamento criado com sucesso!', 'success')
        return redirect(url_for('agendamentos'))
    
    return render_template('agendar.html', form=form)

@app.route('/agendamento/<int:agendamento_id>/atualizar', methods=['POST'])
@login_required
def atualizar_status_agendamento(agendamento_id):
    """
    Rota para atualizar o status de um agendamento.
    """
    form = AtualizarStatusAgendamentoForm()
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if not (current_user.is_master() or 
            (current_user.is_funcionario() and agendamento.funcionario.usuario_id == current_user.id) or
            (not current_user.is_master() and not current_user.is_funcionario() and agendamento.cliente_id == current_user.id)):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('agendamentos'))
    
    if form.validate_on_submit():
        status_antigo = agendamento.status
        agendamento.status = form.status.data
        if form.observacoes.data:
            agendamento.observacoes = form.observacoes.data
        
        db.session.commit()
        
        flash(f'Status do agendamento atualizado de "{status_antigo}" para "{form.status.data}".', 'success')
    
    return redirect(url_for('agendamentos'))

@app.route('/agendamento/<int:agendamento_id>/editar', methods=['GET', 'POST'])
@login_required
def agendamento_editar(agendamento_id):
    """
    Rota para editar um agendamento.
    """
    agendamento = Agendamento.query.get_or_404(agendamento_id)
    
    if not (current_user.is_master() or 
            (current_user.is_funcionario() and agendamento.funcionario.usuario_id == current_user.id) or
            (not current_user.is_master() and not current_user.is_funcionario() and agendamento.cliente_id == current_user.id)):
        flash('Acesso negado.', 'danger')
        return redirect(url_for('agendamentos'))
    
    form = AtualizarStatusAgendamentoForm()
    if request.method == 'GET':
        form.status.data = agendamento.status
        form.observacoes.data = agendamento.observacoes
    
    if form.validate_on_submit():
        status_antigo = agendamento.status
        agendamento.status = form.status.data
        if form.observacoes.data:
            agendamento.observacoes = form.observacoes.data
        
        db.session.commit()
        
        flash(f'Agendamento atualizado com sucesso.', 'success')
        return redirect(url_for('agendamentos'))
    
    return render_template('agendamento_form.html', form=form, agendamento=agendamento, titulo="Editar Agendamento")

@app.route('/relatorios')
@login_required
@permission_required('pode_ver_relatorios')
def relatorios():
    """
    Exibe relatórios estatísticos.
    """
    hoje = datetime.utcnow().date()
    inicio_mes = hoje.replace(day=1)
    
    dados_relatorio = {
        'agendamentos_hoje': Agendamento.query.filter(
            func.date(Agendamento.data_agendamento) == hoje
        ).count(),
        'agendamentos_mes': Agendamento.query.filter(
            func.date(Agendamento.data_agendamento) >= inicio_mes
        ).count(),
        'agendamentos_concluidos': Agendamento.query.filter_by(status='concluido').count(),
        'agendamentos_cancelados': Agendamento.query.filter_by(status='cancelado').count(),
        'funcionarios_ativos': Funcionario.query.filter_by(ativo=True).count(),
        'total_clientes': Usuario.query.filter(
            Usuario.tipo_usuario == 'restrito',
            Usuario.ativo == True,
            Usuario.perfil_funcionario == None
        ).count()
    }
    
    stats_mensais = db.session.query(
        func.extract('month', Agendamento.data_agendamento).label('mes'),
        func.count(Agendamento.id).label('count')
    ).filter(
        func.extract('year', Agendamento.data_agendamento) == datetime.utcnow().year
    ).group_by(
        func.extract('month', Agendamento.data_agendamento)
    ).all()
    
    return render_template('relatorios.html', dados_relatorio=dados_relatorio, stats_mensais=stats_mensais)

@app.route('/bot-whatsapp', methods=['GET'])
@login_required
@master_required
def bot_whatsapp():
    # Redireciona para a subrota padrão (API)
    return redirect(url_for('bot_whatsapp_api'))

@app.route('/bot-whatsapp/api', methods=['GET', 'POST'])
@login_required
@master_required
def bot_whatsapp_api():
    """
    Configuração da API do WhatsApp (tokens e IDs).
    """
    config = ConfiguracaoEmpresa.query.first()
    if not config:
        config = ConfiguracaoEmpresa()
        db.session.add(config)
        db.session.commit()
    
    form = ConfiguracaoBotWhatsAppForm(obj=config)
    
    if form.validate_on_submit():
        config.whatsapp_token = form.whatsapp_token.data
        config.whatsapp_phone_id = form.whatsapp_phone_id.data
        config.whatsapp_webhook_verify_token = form.whatsapp_webhook_verify_token.data
        
        db.session.commit()
        flash('Configurações da API do WhatsApp atualizadas com sucesso!', 'success')
        return redirect(url_for('bot_whatsapp_api'))
    
    return render_template('bot_whatsapp.html', form=form, config=config)

@app.route('/bot-whatsapp/configurar', methods=['GET', 'POST'])
@login_required
@master_required
def bot_whatsapp_configurar():
    """
    Configurações do comportamento do Bot (templates de mensagem, horários, etc.).
    Esta rota apresenta um formulário básico de configuração do bot.
    """
    if request.method == 'POST':
        flash('Configurações do Bot salvas com sucesso!', 'success')
        return redirect(url_for('bot_whatsapp_configurar'))
    return render_template('bot_config.html')

@app.route('/bot-whatsapp/fluxo', methods=['GET', 'POST'])
@login_required
@master_required
def bot_whatsapp_fluxo():
    """
    Editor de Fluxo do Bot (fluxograma). O usuário define nós e conexões.
    """
    if request.method == 'POST':
        flow_json = request.form.get('flow_json')
        # Aqui poderíamos persistir o JSON do fluxo em um storage/DB
        flash('Fluxo do Bot salvo com sucesso!', 'success')
        return redirect(url_for('bot_whatsapp_fluxo'))
    return render_template('bot_fluxo.html')

@app.route('/bot-whatsapp/geral', methods=['GET', 'POST'])
@login_required
@master_required
def bot_whatsapp_geral():
    """
    Configurações gerais do Bot (horários de atendimento, timezone, limites, etc.).
    """
    if request.method == 'POST':
        # Capturar campos
        horario_inicio = request.form.get('horario_inicio')
        horario_fim = request.form.get('horario_fim')
        dias_semana = request.form.getlist('dias_semana')
        timezone = request.form.get('timezone')
        msg_fora = request.form.get('msg_fora_horario')

        # Persistir em ConfiguracaoEmpresa (como exemplo simples)
        config = ConfiguracaoEmpresa.query.first()
        if not config:
            config = ConfiguracaoEmpresa()
            db.session.add(config)
            db.session.commit()

        # Guardar em campos reutilizados (ou seria ideal criar novas colunas)
        # Aqui usamos whatsapp_webhook_verify_token para armazenar JSON (exemplo)
        import json
        blob = {
            'horario_inicio': horario_inicio,
            'horario_fim': horario_fim,
            'dias_semana': dias_semana,
            'timezone': timezone,
            'msg_fora_horario': msg_fora
        }
        config.whatsapp_webhook_verify_token = json.dumps(blob)
        db.session.commit()

        flash('Configurações gerais do Bot salvas com sucesso!', 'success')
        return redirect(url_for('bot_whatsapp_geral'))
    return render_template('bot_geral.html')

@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
@master_required
def configuracoes():
    """
    Configurações gerais da empresa.
    """
    config = ConfiguracaoEmpresa.query.first()
    if not config:
        config = ConfiguracaoEmpresa()
        db.session.add(config)
        db.session.commit()
    
    form = ConfiguracaoEmpresaForm(obj=config)
    
    if form.validate_on_submit():
        config.nome_empresa = form.nome_empresa.data
        
        if form.logo.data:
            filename = secure_filename(form.logo.data.filename)
            if filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                form.logo.data.save(filepath)
                config.logo_path = filename
        
        db.session.commit()
        flash('Configurações da empresa atualizadas com sucesso!', 'success')
        return redirect(url_for('configuracoes'))
    
    return render_template('configuracoes.html', form=form, config=config)

@app.context_processor
def inject_config():
    """
    Injeta a configuração da empresa em todos os templates.
    """
    config = ConfiguracaoEmpresa.query.first()
    return dict(empresa_config=config)

@app.route('/api/search/clientes')
@login_required
def api_search_clientes():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    clientes = Usuario.query.filter(
        and_(
            Usuario.ativo.is_(True),
            Usuario.tipo_usuario == 'restrito',
            Usuario.perfil_funcionario == None,
            Usuario.nome.ilike(f"%{q}%")
        )
    ).order_by(Usuario.nome).limit(10).all()
    return jsonify([{'id': c.id, 'label': f"{c.nome} ({c.email})"} for c in clientes])

@app.route('/api/search/funcionarios')
@login_required
def api_search_funcionarios():
    q = (request.args.get('q') or '').strip()
    if not q:
        return jsonify([])
    funcionarios = Funcionario.query.join(Usuario).filter(
        and_(
            Funcionario.ativo.is_(True),
            Usuario.ativo.is_(True),
            Usuario.nome.ilike(f"%{q}%")
        )
    ).order_by(Usuario.nome).limit(10).all()
    return jsonify([{'id': f.id, 'label': f"{f.usuario.nome} - {f.cargo.nome}"} for f in funcionarios])