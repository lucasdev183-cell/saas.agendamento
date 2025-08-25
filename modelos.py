from aplicacao import db
from flask_login import UserMixin
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import re
import json
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy import func, case

class Usuario(UserMixin, db.Model):
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    tipo_usuario = db.Column(db.String(20), default='restrito')  # master, restrito
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20))
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Campos adicionais para clientes
    cpf_cnpj = db.Column(db.String(18))  # CPF ou CNPJ
    endereco = db.Column(db.String(255))
    cidade = db.Column(db.String(100))
    estado = db.Column(db.String(2))
    cep = db.Column(db.String(10))
    data_nascimento = db.Column(db.Date)
    observacoes = db.Column(db.Text)
    
    # Controle de segurança
    ultimo_login = db.Column(db.DateTime)
    tentativas_login = db.Column(db.Integer, default=0)
    bloqueado_ate = db.Column(db.DateTime)
    requer_alteracao_senha = db.Column(db.Boolean, default=False)
    
    # Permissões específicas para usuários restritos
    pode_cadastrar_cliente = db.Column(db.Boolean, default=False)
    pode_cadastrar_funcionario = db.Column(db.Boolean, default=False)
    pode_cadastrar_cargo = db.Column(db.Boolean, default=False)
    pode_cadastrar_servico = db.Column(db.Boolean, default=False)
    pode_agendar = db.Column(db.Boolean, default=True)
    pode_ver_agendamentos = db.Column(db.Boolean, default=True)
    pode_ver_relatorios = db.Column(db.Boolean, default=False)
    pode_configurar_sistema = db.Column(db.Boolean, default=False)
    
    # Relationships
    perfil_funcionario = db.relationship('Funcionario', backref='usuario', uselist=False)
    agendamentos_cliente = db.relationship('Agendamento', foreign_keys='Agendamento.cliente_id', backref='cliente')

    def set_password(self, password):
        """Define uma nova senha para o usuário"""
        self.password_hash = generate_password_hash(password)
        self.requer_alteracao_senha = False

    def check_password(self, password):
        """Verifica se a senha está correta"""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_master(self):
        return self.tipo_usuario == 'master'

    def is_funcionario(self):
        return self.perfil_funcionario is not None
    
    def is_cliente(self):
        """Verifica se é um cliente (não é funcionário e nem master)"""
        return self.tipo_usuario == 'restrito' and not self.is_funcionario()
    
    def is_blocked(self):
        """Verifica se o usuário está bloqueado"""
        if self.bloqueado_ate:
            return datetime.utcnow() < self.bloqueado_ate
        return False
    
    def block_user(self, minutes=30):
        """Bloqueia o usuário por um período específico"""
        self.bloqueado_ate = datetime.utcnow() + timedelta(minutes=minutes)
        
    def unblock_user(self):
        """Desbloqueia o usuário"""
        self.bloqueado_ate = None
        self.tentativas_login = 0
    
    def register_login_attempt(self, success=True):
        """Registra tentativa de login"""
        if success:
            self.ultimo_login = datetime.utcnow()
            self.tentativas_login = 0
            self.bloqueado_ate = None
        else:
            self.tentativas_login += 1
            if self.tentativas_login >= 5:
                self.block_user(30)  # Bloqueia por 30 minutos
    
    @staticmethod
    def validate_cpf(cpf):
        """Valida CPF brasileiro"""
        if not cpf:
            return True  # CPF é opcional
        cpf = re.sub(r'[^0-9]', '', cpf)
        if len(cpf) != 11:
            return False
        if cpf == cpf[0] * 11:  # Todos os dígitos iguais
            return False
        
        # Cálculo do primeiro dígito verificador
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        primeiro_dv = (soma * 10) % 11
        if primeiro_dv == 10:
            primeiro_dv = 0
        
        if int(cpf[9]) != primeiro_dv:
            return False
        
        # Cálculo do segundo dígito verificador
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        segundo_dv = (soma * 10) % 11
        if segundo_dv == 10:
            segundo_dv = 0
        
        return int(cpf[10]) == segundo_dv
    
    @staticmethod
    def validate_cnpj(cnpj):
        """Valida CNPJ brasileiro"""
        if not cnpj:
            return True  # CNPJ é opcional
        cnpj = re.sub(r'[^0-9]', '', cnpj)
        if len(cnpj) != 14:
            return False
        if cnpj == cnpj[0] * 14:  # Todos os dígitos iguais
            return False
        
        # Algoritmo de validação do CNPJ
        multiplicadores1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        multiplicadores2 = [6, 7, 8, 9, 2, 3, 4, 5, 6, 7, 8, 9]
        
        soma1 = sum(int(cnpj[i]) * multiplicadores1[i] for i in range(12))
        resto1 = soma1 % 11
        dv1 = 0 if resto1 < 2 else 11 - resto1
        
        if int(cnpj[12]) != dv1:
            return False
        
        soma2 = sum(int(cnpj[i]) * multiplicadores2[i] for i in range(13))
        resto2 = soma2 % 11
        dv2 = 0 if resto2 < 2 else 11 - resto2
        
        return int(cnpj[13]) == dv2
    
    def validate_cpf_cnpj(self):
        """Valida CPF ou CNPJ do usuário"""
        if not self.cpf_cnpj:
            return True
        
        # Remove formatação
        documento = re.sub(r'[^0-9]', '', self.cpf_cnpj)
        
        if len(documento) == 11:
            return self.validate_cpf(documento)
        elif len(documento) == 14:
            return self.validate_cnpj(documento)
        else:
            return False
    
    @property
    def total_agendamentos(self):
        """Retorna o total de agendamentos do cliente"""
        if self.is_cliente():
            return len(self.agendamentos_cliente)
        return 0
    
    @property
    def agendamentos_pendentes(self):
        """Retorna agendamentos pendentes do cliente"""
        if self.is_cliente():
            return [a for a in self.agendamentos_cliente if a.status == 'agendado']
        return []
    
    @property
    def ultimo_agendamento(self):
        """Retorna o último agendamento do cliente"""
        if self.is_cliente() and self.agendamentos_cliente:
            return max(self.agendamentos_cliente, key=lambda x: x.data_agendamento)
        return None
    
    def to_dict(self):
        """Converte o usuário para dicionário (útil para APIs)"""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nome': self.nome,
            'telefone': self.telefone,
            'tipo_usuario': self.tipo_usuario,
            'ativo': self.ativo,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None,
            'ultimo_login': self.ultimo_login.isoformat() if self.ultimo_login else None,
            'is_funcionario': self.is_funcionario(),
            'is_cliente': self.is_cliente(),
            'total_agendamentos': self.total_agendamentos
        }

    def __repr__(self):
        return f'<Usuario {self.username}>'

class Cargo(db.Model):
    __tablename__ = 'cargos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Hierarquia organizacional
    cargo_pai_id = db.Column(db.Integer, db.ForeignKey('cargos.id'))
    nivel_hierarquico = db.Column(db.Integer, default=1)
    
    # Configurações do cargo
    salario_base = db.Column(db.Float)
    percentual_comissao = db.Column(db.Float, default=0.0)
    carga_horaria_semanal = db.Column(db.Integer, default=40)
    
    # Permissões específicas do cargo
    permissoes_json = db.Column(db.Text)  # JSON com permissões específicas
    
    # Relationships
    funcionarios = db.relationship('Funcionario', backref='cargo')
    cargos_filhos = db.relationship('Cargo', backref=db.backref('cargo_pai', remote_side=[id]))
    
    @property
    def permissoes(self):
        """Retorna as permissões do cargo como dicionário"""
        if self.permissoes_json:
            try:
                return json.loads(self.permissoes_json)
            except json.JSONDecodeError:
                return {}
        return {}
    
    @permissoes.setter
    def permissoes(self, valor):
        """Define as permissões do cargo"""
        if isinstance(valor, dict):
            self.permissoes_json = json.dumps(valor)
        else:
            self.permissoes_json = None
    
    def get_permissao(self, chave, default=False):
        """Obtém uma permissão específica"""
        return self.permissoes.get(chave, default)
    
    def set_permissao(self, chave, valor):
        """Define uma permissão específica"""
        permissoes = self.permissoes
        permissoes[chave] = valor
        self.permissoes = permissoes
    
    @property
    def funcionarios_ativos(self):
        """Retorna funcionários ativos deste cargo"""
        return [f for f in self.funcionarios if f.ativo]
    
    @property
    def total_funcionarios(self):
        """Retorna o total de funcionários neste cargo"""
        return len(self.funcionarios_ativos)
    
    def to_dict(self):
        """Converte o cargo para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'ativo': self.ativo,
            'nivel_hierarquico': self.nivel_hierarquico,
            'salario_base': self.salario_base,
            'percentual_comissao': self.percentual_comissao,
            'total_funcionarios': self.total_funcionarios,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

    def __repr__(self):
        return f'<Cargo {self.nome}>'
    
class CategoriaServico(db.Model):
    __tablename__ = 'categorias_servico'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    ordem = db.Column(db.Integer, default=0)
    cor = db.Column(db.String(7), default='#007bff')  # Cor hexadecimal
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    servicos = db.relationship('Servico', backref='categoria')
    
    def __repr__(self):
        return f'<CategoriaServico {self.nome}>'

class Servico(db.Model):
    __tablename__ = 'servicos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text, nullable=True)
    preco = db.Column(db.Float, nullable=False)
    duracao_minutos = db.Column(db.Integer, nullable=False)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Categoria e organização
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias_servico.id'))
    ordem = db.Column(db.Integer, default=0)
    
    # Configurações avançadas
    preco_promocional = db.Column(db.Float)
    data_inicio_promocao = db.Column(db.DateTime)
    data_fim_promocao = db.Column(db.DateTime)
    
    # Configurações de agendamento
    intervalo_entre_agendamentos = db.Column(db.Integer, default=0)  # em minutos
    max_agendamentos_dia = db.Column(db.Integer)
    antecedencia_minima_horas = db.Column(db.Integer, default=1)
    
    # Comissão e custos
    custo = db.Column(db.Float, default=0.0)
    percentual_comissao = db.Column(db.Float, default=0.0)
    
    # Estatísticas
    total_agendamentos = db.Column(db.Integer, default=0)
    avaliacao_media = db.Column(db.Float, default=0.0)
    
    # Relationships
    agendamentos = db.relationship('Agendamento', foreign_keys='Agendamento.servico_id', backref='servico')
    
    @property
    def preco_atual(self):
        """Retorna o preço atual considerando promoções"""
        if self.em_promocao:
            return self.preco_promocional or self.preco
        return self.preco
    
    @property
    def em_promocao(self):
        """Verifica se o serviço está em promoção"""
        if not self.preco_promocional or not self.data_inicio_promocao or not self.data_fim_promocao:
            return False
        
        agora = datetime.utcnow()
        return self.data_inicio_promocao <= agora <= self.data_fim_promocao
    
    @property
    def margem_lucro(self):
        """Calcula a margem de lucro do serviço"""
        if self.custo > 0:
            return ((self.preco_atual - self.custo) / self.preco_atual) * 100
        return 100.0
    
    @property
    def popularidade(self):
        """Calcula a popularidade baseada no número de agendamentos"""
        if self.total_agendamentos == 0:
            return 0
        
        # Considera também agendamentos recentes (últimos 30 dias)
        agendamentos_recentes = len([a for a in self.agendamentos 
                                   if a.criado_em and 
                                   a.criado_em >= datetime.utcnow() - timedelta(days=30)])
        
        return min(100, (agendamentos_recentes / 10) * 100)  # Max 100%
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas do serviço"""
        self.total_agendamentos = len(self.agendamentos)
        
        # Calcular avaliação média (se houver sistema de avaliação)
        agendamentos_concluidos = [a for a in self.agendamentos if a.status == 'concluido']
        if agendamentos_concluidos:
            # Aqui poderia calcular média de avaliações se existisse o campo
            self.avaliacao_media = 5.0  # Placeholder
    
    def definir_promocao(self, preco_promocional, data_inicio, data_fim):
        """Define uma promoção para o serviço"""
        self.preco_promocional = preco_promocional
        self.data_inicio_promocao = data_inicio
        self.data_fim_promocao = data_fim
    
    def remover_promocao(self):
        """Remove a promoção do serviço"""
        self.preco_promocional = None
        self.data_inicio_promocao = None
        self.data_fim_promocao = None
    
    def to_dict(self):
        """Converte o serviço para dicionário"""
        return {
            'id': self.id,
            'nome': self.nome,
            'descricao': self.descricao,
            'preco': self.preco,
            'preco_atual': self.preco_atual,
            'em_promocao': self.em_promocao,
            'duracao_minutos': self.duracao_minutos,
            'ativo': self.ativo,
            'categoria': self.categoria.nome if self.categoria else None,
            'total_agendamentos': self.total_agendamentos,
            'popularidade': self.popularidade,
            'margem_lucro': self.margem_lucro,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

    def __repr__(self):
        return f'<Servico {self.nome}>'    

class EspecialidadeFuncionario(db.Model):
    __tablename__ = 'especialidades_funcionario'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    ativo = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<EspecialidadeFuncionario {self.nome}>'

# Tabela de associação para funcionários e especialidades
funcionario_especialidades = db.Table('funcionario_especialidades',
    db.Column('funcionario_id', db.Integer, db.ForeignKey('funcionarios.id'), primary_key=True),
    db.Column('especialidade_id', db.Integer, db.ForeignKey('especialidades_funcionario.id'), primary_key=True)
)

# Tabela de associação para funcionários e serviços que podem executar
funcionario_servicos = db.Table('funcionario_servicos',
    db.Column('funcionario_id', db.Integer, db.ForeignKey('funcionarios.id'), primary_key=True),
    db.Column('servico_id', db.Integer, db.ForeignKey('servicos.id'), primary_key=True)
)

class Funcionario(db.Model):
    __tablename__ = 'funcionarios'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cargo_id = db.Column(db.Integer, db.ForeignKey('cargos.id'), nullable=False)
    data_contratacao = db.Column(db.Date, default=datetime.utcnow().date)
    ativo = db.Column(db.Boolean, default=True)
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Informações profissionais
    registro_profissional = db.Column(db.String(50))  # CRM, CRO, etc.
    observacoes = db.Column(db.Text)
    
    # Configurações de trabalho
    horario_inicio = db.Column(db.Time, default=lambda: datetime.strptime('08:00', '%H:%M').time())
    horario_fim = db.Column(db.Time, default=lambda: datetime.strptime('18:00', '%H:%M').time())
    trabalha_sabado = db.Column(db.Boolean, default=False)
    trabalha_domingo = db.Column(db.Boolean, default=False)
    
    # Configurações de comissão
    tipo_comissao = db.Column(db.String(20), default='percentual')  # percentual, valor_fixo
    valor_comissao = db.Column(db.Float, default=0.0)
    
    # Estatísticas
    total_agendamentos = db.Column(db.Integer, default=0)
    total_agendamentos_concluidos = db.Column(db.Integer, default=0)
    avaliacao_media = db.Column(db.Float, default=0.0)
    
    # Relationships
    agendamentos = db.relationship('Agendamento', foreign_keys='Agendamento.funcionario_id', backref='funcionario')
    especialidades = db.relationship('EspecialidadeFuncionario', 
                                   secondary=funcionario_especialidades, 
                                   backref='funcionarios')
    servicos_habilitados = db.relationship('Servico', 
                                         secondary=funcionario_servicos, 
                                         backref='funcionarios_habilitados')
    
    @property
    def disponivel_hoje(self):
        """Verifica se o funcionário está disponível hoje"""
        if not self.ativo:
            return False
        
        hoje = datetime.now().weekday()  # 0=Segunda, 6=Domingo
        
        if hoje == 5 and not self.trabalha_sabado:  # Sábado
            return False
        if hoje == 6 and not self.trabalha_domingo:  # Domingo
            return False
        
        return True
    
    @property
    def taxa_conclusao(self):
        """Calcula a taxa de conclusão de agendamentos"""
        if self.total_agendamentos == 0:
            return 0
        return (self.total_agendamentos_concluidos / self.total_agendamentos) * 100
    
    @property
    def agendamentos_hoje(self):
        """Retorna agendamentos para hoje"""
        hoje = datetime.now().date()
        return [a for a in self.agendamentos 
                if a.data_agendamento.date() == hoje and a.status == 'agendado']
    
    @property
    def agendamentos_semana(self):
        """Retorna agendamentos da semana atual"""
        hoje = datetime.now().date()
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        fim_semana = inicio_semana + timedelta(days=6)
        
        return [a for a in self.agendamentos 
                if inicio_semana <= a.data_agendamento.date() <= fim_semana]
    
    def calcular_comissao_periodo(self, data_inicio, data_fim):
        """Calcula a comissão do funcionário em um período"""
        agendamentos_periodo = [a for a in self.agendamentos 
                              if data_inicio <= a.data_agendamento.date() <= data_fim 
                              and a.status == 'concluido']
        
        total_comissao = 0.0
        for agendamento in agendamentos_periodo:
            if agendamento.servico_id:
                servico = agendamento.servico
                if self.tipo_comissao == 'percentual':
                    # Usa comissão do cargo ou do funcionário
                    percentual = self.valor_comissao or self.cargo.percentual_comissao or 0
                    total_comissao += (servico.preco_atual * percentual / 100)
                else:
                    total_comissao += self.valor_comissao or 0
        
        return total_comissao
    
    def atualizar_estatisticas(self):
        """Atualiza as estatísticas do funcionário"""
        self.total_agendamentos = len(self.agendamentos)
        self.total_agendamentos_concluidos = len([a for a in self.agendamentos 
                                                if a.status == 'concluido'])
        
        # Calcular avaliação média (se houver sistema de avaliação)
        if self.total_agendamentos_concluidos > 0:
            self.avaliacao_media = 4.5  # Placeholder
    
    def pode_executar_servico(self, servico_id):
        """Verifica se o funcionário pode executar um serviço"""
        return servico_id in [s.id for s in self.servicos_habilitados]
    
    def adicionar_servico(self, servico):
        """Adiciona um serviço que o funcionário pode executar"""
        if servico not in self.servicos_habilitados:
            self.servicos_habilitados.append(servico)
    
    def remover_servico(self, servico):
        """Remove um serviço que o funcionário pode executar"""
        if servico in self.servicos_habilitados:
            self.servicos_habilitados.remove(servico)
    
    def to_dict(self):
        """Converte o funcionário para dicionário"""
        return {
            'id': self.id,
            'nome': self.usuario.nome,
            'email': self.usuario.email,
            'cargo': self.cargo.nome,
            'ativo': self.ativo,
            'data_contratacao': self.data_contratacao.isoformat() if self.data_contratacao else None,
            'registro_profissional': self.registro_profissional,
            'total_agendamentos': self.total_agendamentos,
            'taxa_conclusao': self.taxa_conclusao,
            'avaliacao_media': self.avaliacao_media,
            'disponivel_hoje': self.disponivel_hoje,
            'especialidades': [e.nome for e in self.especialidades],
            'servicos_habilitados': [s.nome for s in self.servicos_habilitados]
        }

    def __repr__(self):
        return f'<Funcionario {self.usuario.nome}>'

class Agendamento(db.Model):
    __tablename__ = 'agendamentos'
    
    id = db.Column(db.Integer, primary_key=True)
    cliente_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    funcionario_id = db.Column(db.Integer, db.ForeignKey('funcionarios.id'), nullable=False)
    servico_id = db.Column(db.Integer, db.ForeignKey('servicos.id'), nullable=False)
    data_agendamento = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='agendado')  # agendado, concluido, cancelado
    observacoes = db.Column(db.Text)
    
    # Campos legados para compatibilidade
    servico = db.Column(db.String(200))  # Manter para compatibilidade
    duracao_minutos = db.Column(db.Integer, default=60)
    
    # Campos adicionais
    preco_cobrado = db.Column(db.Float)  # Preço no momento do agendamento
    desconto_aplicado = db.Column(db.Float, default=0.0)
    valor_final = db.Column(db.Float)
    
    # Controle de tempo
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_cancelamento = db.Column(db.DateTime)
    data_conclusao = db.Column(db.DateTime)
    
    # Avaliação
    avaliacao = db.Column(db.Integer)  # 1-5 estrelas
    comentario_avaliacao = db.Column(db.Text)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Define preço cobrado baseado no serviço
        if self.servico_id and not self.preco_cobrado:
            from . import Servico  # Import local para evitar circular
            servico = Servico.query.get(self.servico_id)
            if servico:
                self.preco_cobrado = servico.preco_atual
                self.valor_final = self.preco_cobrado
    
    @property
    def data_fim(self):
        """Calcula a data/hora de fim do agendamento"""
        if self.servico_id:
            duracao = self.servico.duracao_minutos
        else:
            duracao = self.duracao_minutos or 60
        
        return self.data_agendamento + timedelta(minutes=duracao)
    
    @property
    def duracao_real(self):
        """Retorna a duração real baseada no serviço"""
        if self.servico_id:
            return self.servico.duracao_minutos
        return self.duracao_minutos or 60
    
    @property
    def pode_cancelar(self):
        """Verifica se o agendamento pode ser cancelado"""
        if self.status != 'agendado':
            return False
        
        # Verifica antecedência mínima
        agora = datetime.utcnow()
        if self.servico_id:
            antecedencia = self.servico.antecedencia_minima_horas or 1
        else:
            antecedencia = 1
        
        return self.data_agendamento > agora + timedelta(hours=antecedencia)
    
    @property
    def tempo_restante(self):
        """Retorna o tempo restante até o agendamento"""
        if self.status != 'agendado':
            return None
        
        agora = datetime.utcnow()
        if self.data_agendamento > agora:
            delta = self.data_agendamento - agora
            return {
                'days': delta.days,
                'hours': delta.seconds // 3600,
                'minutes': (delta.seconds % 3600) // 60
            }
        return None
    
    def cancelar(self, motivo=None):
        """Cancela o agendamento"""
        if self.pode_cancelar:
            self.status = 'cancelado'
            self.data_cancelamento = datetime.utcnow()
            if motivo:
                self.observacoes = f"{self.observacoes or ''}\nCancelado: {motivo}".strip()
            return True
        return False
    
    def concluir(self, observacoes_conclusao=None):
        """Marca o agendamento como concluído"""
        if self.status == 'agendado':
            self.status = 'concluido'
            self.data_conclusao = datetime.utcnow()
            if observacoes_conclusao:
                self.observacoes = f"{self.observacoes or ''}\nConclusão: {observacoes_conclusao}".strip()
            return True
        return False
    
    def aplicar_desconto(self, percentual=None, valor=None):
        """Aplica desconto ao agendamento"""
        if not self.preco_cobrado:
            return False
        
        if percentual:
            self.desconto_aplicado = (self.preco_cobrado * percentual / 100)
        elif valor:
            self.desconto_aplicado = min(valor, self.preco_cobrado)
        
        self.valor_final = self.preco_cobrado - self.desconto_aplicado
        return True
    
    def avaliar(self, nota, comentario=None):
        """Adiciona avaliação ao agendamento"""
        if self.status == 'concluido' and 1 <= nota <= 5:
            self.avaliacao = nota
            self.comentario_avaliacao = comentario
            return True
        return False
    
    def to_dict(self):
        """Converte o agendamento para dicionário"""
        return {
            'id': self.id,
            'cliente': self.cliente.nome,
            'funcionario': self.funcionario.usuario.nome,
            'servico': self.servico.nome if self.servico_id else self.servico,
            'data_agendamento': self.data_agendamento.isoformat(),
            'data_fim': self.data_fim.isoformat(),
            'status': self.status,
            'preco_cobrado': self.preco_cobrado,
            'desconto_aplicado': self.desconto_aplicado,
            'valor_final': self.valor_final,
            'avaliacao': self.avaliacao,
            'pode_cancelar': self.pode_cancelar,
            'tempo_restante': self.tempo_restante,
            'criado_em': self.criado_em.isoformat() if self.criado_em else None
        }

    def __repr__(self):
        return f'<Agendamento {self.id} - {self.cliente.nome}>'

class LogAuditoria(db.Model):
    __tablename__ = 'logs_auditoria'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=True)
    acao = db.Column(db.String(100), nullable=False)
    tabela = db.Column(db.String(50), nullable=False)
    registro_id = db.Column(db.Integer)
    valores_antigos = db.Column(db.Text)
    valores_novos = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    ip_address = db.Column(db.String(45))

    def __repr__(self):
        return f'<LogAuditoria {self.acao} em {self.tabela}>'

class ConfiguracaoEmpresa(db.Model):
    __tablename__ = 'configuracao_empresa'
    
    id = db.Column(db.Integer, primary_key=True)
    nome_empresa = db.Column(db.String(200), nullable=False, default='JT Sistemas')
    logo_path = db.Column(db.String(500))
    whatsapp_token = db.Column(db.String(500))
    whatsapp_phone_id = db.Column(db.String(100))
    whatsapp_webhook_verify_token = db.Column(db.String(200))
    atualizado_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ConfiguracaoEmpresa {self.nome_empresa}>'
