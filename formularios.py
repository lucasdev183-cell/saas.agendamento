from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
# Importe os novos tipos de campo e validadores aqui
from wtforms import (StringField, PasswordField, SelectField, TextAreaField, 
                     DateTimeField, IntegerField, BooleanField, FloatField, SubmitField,
                     DateField, TimeField, SelectMultipleField, HiddenField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo, Optional, 
                                NumberRange, ValidationError, Regexp)
from wtforms.widgets import DateTimeInput, DateInput, TimeInput, CheckboxInput, TextArea
import re

# Importe o novo modelo 'Servico' para usar no AgendamentoForm
from modelos import Cargo, Funcionario, Servico, CategoriaServico, EspecialidadeFuncionario

class LoginForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    password = PasswordField('Senha', validators=[DataRequired()])

class CadastroUsuarioForm(FlaskForm):
    username = StringField('Usuário', validators=[DataRequired(), Length(min=3, max=80)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    password = PasswordField('Senha', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Confirmar Senha', 
                             validators=[DataRequired(), EqualTo('password', message='Senhas devem ser iguais')])
    tipo_usuario = SelectField('Tipo de Usuário', 
                              choices=[('restrito', 'Usuário Restrito')],
                              default='restrito')
    
    # Permissões para usuários restritos
    pode_cadastrar_cliente = BooleanField('Pode Cadastrar Clientes')
    pode_cadastrar_funcionario = BooleanField('Pode Cadastrar Funcionários')
    pode_cadastrar_cargo = BooleanField('Pode Cadastrar Cargos')
    pode_agendar = BooleanField('Pode Agendar', default=True)
    pode_ver_agendamentos = BooleanField('Pode Ver Agendamentos', default=True)
    pode_ver_relatorios = BooleanField('Pode Ver Relatórios')

class UsuarioEditForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    ativo = BooleanField('Ativo', default=True)
    pode_cadastrar_cliente = BooleanField('Pode Cadastrar Clientes')
    pode_cadastrar_funcionario = BooleanField('Pode Cadastrar Funcionários')
    pode_cadastrar_cargo = BooleanField('Pode Cadastrar Cargos')
    pode_agendar = BooleanField('Pode Agendar')
    pode_ver_agendamentos = BooleanField('Pode Ver Agendamentos')
    pode_ver_relatorios = BooleanField('Pode Ver Relatórios')
    submit = SubmitField('Salvar')

class CadastroClienteForm(FlaskForm):
    # Campos básicos
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    nome = StringField('Nome Completo', validators=[DataRequired(), Length(min=2, max=100)])
    telefone = StringField('Telefone', validators=[Optional(), Length(max=20)])
    
    # Campos adicionais
    cpf_cnpj = StringField('CPF/CNPJ', validators=[Optional(), Length(max=18)])
    data_nascimento = DateField('Data de Nascimento', 
                               validators=[Optional()], 
                               widget=DateInput())
    
    # Endereço
    endereco = StringField('Endereço', validators=[Optional(), Length(max=255)])
    cidade = StringField('Cidade', validators=[Optional(), Length(max=100)])
    estado = SelectField('Estado', 
                        choices=[('', 'Selecione...')] + [
                            ('AC', 'Acre'), ('AL', 'Alagoas'), ('AP', 'Amapá'),
                            ('AM', 'Amazonas'), ('BA', 'Bahia'), ('CE', 'Ceará'),
                            ('DF', 'Distrito Federal'), ('ES', 'Espírito Santo'),
                            ('GO', 'Goiás'), ('MA', 'Maranhão'), ('MT', 'Mato Grosso'),
                            ('MS', 'Mato Grosso do Sul'), ('MG', 'Minas Gerais'),
                            ('PA', 'Pará'), ('PB', 'Paraíba'), ('PR', 'Paraná'),
                            ('PE', 'Pernambuco'), ('PI', 'Piauí'), ('RJ', 'Rio de Janeiro'),
                            ('RN', 'Rio Grande do Norte'), ('RS', 'Rio Grande do Sul'),
                            ('RO', 'Rondônia'), ('RR', 'Roraima'), ('SC', 'Santa Catarina'),
                            ('SP', 'São Paulo'), ('SE', 'Sergipe'), ('TO', 'Tocantins')
                        ],
                        validators=[Optional()])
    cep = StringField('CEP', 
                     validators=[Optional(), 
                                Regexp(r'^\d{5}-?\d{3}$', 
                                      message='CEP deve ter o formato 00000-000')])
    
    observacoes = TextAreaField('Observações', 
                               validators=[Optional(), Length(max=500)],
                               widget=TextArea())
    
    def validate_cpf_cnpj(self, field):
        """Validação customizada para CPF/CNPJ"""
        if field.data:
            from modelos import Usuario
            if not Usuario.validate_cpf(field.data) and not Usuario.validate_cnpj(field.data):
                raise ValidationError('CPF ou CNPJ inválido.')
    
    def validate_data_nascimento(self, field):
        """Validação customizada para data de nascimento"""
        if field.data:
            from datetime import date
            hoje = date.today()
            if field.data > hoje:
                raise ValidationError('Data de nascimento não pode ser no futuro.')
            if field.data.year < 1900:
                raise ValidationError('Data de nascimento muito antiga.')

class FuncionarioForm(FlaskForm):
    usuario_id = SelectField('Usuário', coerce=int, validators=[DataRequired()])
    cargo_id = SelectField('Cargo', coerce=int, validators=[DataRequired()])
    
    # Informações profissionais
    registro_profissional = StringField('Registro Profissional (CRM, CRO, etc.)', 
                                       validators=[Optional(), Length(max=50)])
    data_contratacao = DateField('Data de Contratação', 
                               validators=[Optional()],
                               widget=DateInput())
    
    # Configurações de trabalho
    horario_inicio = TimeField('Horário de Início', 
                             validators=[Optional()],
                             widget=TimeInput())
    horario_fim = TimeField('Horário de Fim', 
                          validators=[Optional()],
                          widget=TimeInput())
    trabalha_sabado = BooleanField('Trabalha aos Sábados')
    trabalha_domingo = BooleanField('Trabalha aos Domingos')
    
    # Configurações de comissão
    tipo_comissao = SelectField('Tipo de Comissão',
                               choices=[('percentual', 'Percentual'), 
                                       ('valor_fixo', 'Valor Fixo')],
                               default='percentual')
    valor_comissao = FloatField('Valor da Comissão', 
                               validators=[Optional(), NumberRange(min=0)])
    
    # Especialidades
    especialidades = SelectMultipleField('Especialidades', coerce=int)
    servicos_habilitados = SelectMultipleField('Serviços Habilitados', coerce=int)
    
    observacoes = TextAreaField('Observações', 
                               validators=[Optional(), Length(max=500)],
                               widget=TextArea())
    
    ativo = BooleanField('Ativo', default=True)
    
    def __init__(self, *args, **kwargs):
        super(FuncionarioForm, self).__init__(*args, **kwargs)
        # Populate choices dynamically
        from modelos import Usuario
        self.usuario_id.choices = [(u.id, f"{u.nome} ({u.username})") 
                                 for u in Usuario.query.filter(
                                     Usuario.ativo == True,
                                     Usuario.perfil_funcionario == None
                                 ).all()]
        self.cargo_id.choices = [(c.id, c.nome) 
                               for c in Cargo.query.filter_by(ativo=True).all()]
        
        # Carregar especialidades
        self.especialidades.choices = [(e.id, e.nome) 
                                     for e in EspecialidadeFuncionario.query.filter_by(ativo=True).all()]
        
        # Carregar serviços
        self.servicos_habilitados.choices = [(s.id, s.nome) 
                                           for s in Servico.query.filter_by(ativo=True).all()]
    
    def validate_horario_fim(self, field):
        """Validação para garantir que horário de fim seja maior que horário de início"""
        if self.horario_inicio.data and field.data:
            if field.data <= self.horario_inicio.data:
                raise ValidationError('Horário de fim deve ser posterior ao horário de início.')
    
    def validate_data_contratacao(self, field):
        """Validação para data de contratação"""
        if field.data:
            from datetime import date
            hoje = date.today()
            if field.data > hoje:
                raise ValidationError('Data de contratação não pode ser no futuro.')

class CargoForm(FlaskForm):
    nome = StringField('Nome do Cargo', validators=[DataRequired(), Length(min=2, max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])
    
    # Hierarquia
    cargo_pai_id = SelectField('Cargo Superior', coerce=int, validators=[Optional()])
    nivel_hierarquico = IntegerField('Nível Hierárquico', 
                                   validators=[Optional(), NumberRange(min=1, max=10)],
                                   default=1)
    
    # Configurações financeiras
    salario_base = FloatField('Salário Base (R$)', 
                            validators=[Optional(), NumberRange(min=0)])
    percentual_comissao = FloatField('Percentual de Comissão (%)', 
                                   validators=[Optional(), NumberRange(min=0, max=100)])
    carga_horaria_semanal = IntegerField('Carga Horária Semanal', 
                                       validators=[Optional(), NumberRange(min=1, max=60)],
                                       default=40)
    
    # Permissões específicas
    pode_cadastrar_cliente = BooleanField('Pode Cadastrar Clientes')
    pode_cadastrar_funcionario = BooleanField('Pode Cadastrar Funcionários')
    pode_cadastrar_cargo = BooleanField('Pode Cadastrar Cargos')
    pode_cadastrar_servico = BooleanField('Pode Cadastrar Serviços')
    pode_agendar = BooleanField('Pode Agendar', default=True)
    pode_ver_agendamentos = BooleanField('Pode Ver Agendamentos', default=True)
    pode_ver_relatorios = BooleanField('Pode Ver Relatórios')
    pode_configurar_sistema = BooleanField('Pode Configurar Sistema')
    
    ativo = BooleanField('Ativo', default=True)
    
    def __init__(self, *args, **kwargs):
        super(CargoForm, self).__init__(*args, **kwargs)
        # Carregar cargos para hierarquia (excluindo o próprio cargo se for edição)
        cargo_atual_id = kwargs.get('obj', {}).get('id') if hasattr(kwargs.get('obj', {}), 'get') else None
        if hasattr(kwargs.get('obj', None), 'id'):
            cargo_atual_id = kwargs['obj'].id
        
        cargos_choices = [('', 'Nenhum (Cargo Raiz)')]
        for cargo in Cargo.query.filter_by(ativo=True).all():
            if cargo_atual_id is None or cargo.id != cargo_atual_id:
                cargos_choices.append((cargo.id, cargo.nome))
        
        self.cargo_pai_id.choices = cargos_choices

class AgendamentoForm(FlaskForm):
    cliente_id = SelectField('Cliente', coerce=int, validators=[DataRequired()])
    funcionario_id = SelectField('Funcionário', coerce=int, validators=[DataRequired()])
    data_agendamento = DateTimeField('Data e Hora', 
                                    validators=[DataRequired()],
                                    widget=DateTimeInput())
    # O campo de servico agora deve ser um SelectField para o novo modelo de Servico
    servico_id = SelectField('Serviço', coerce=int, validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])
    
    def __init__(self, *args, **kwargs):
        super(AgendamentoForm, self).__init__(*args, **kwargs)
        # Populate choices dynamically
        from modelos import Usuario
        clientes = Usuario.query.filter(
            Usuario.ativo == True,
            Usuario.tipo_usuario == 'restrito',
            Usuario.perfil_funcionario == None
        ).all()
        
        self.cliente_id.choices = [(u.id, f"{u.nome} ({u.email})") for u in clientes]
        self.funcionario_id.choices = [(f.id, f"{f.usuario.nome} - {f.cargo.nome}") 
                                      for f in Funcionario.query.filter_by(ativo=True).all()]
        self.servico_id.choices = [(s.id, f"{s.nome} - R$ {s.preco:.2f}")
                                  for s in Servico.query.filter_by(ativo=True).all()]

class AtualizarStatusAgendamentoForm(FlaskForm):
    status = SelectField('Status', 
                         choices=[('agendado', 'Agendado'), 
                                  ('concluido', 'Concluído'), 
                                  ('cancelado', 'Cancelado')],
                         validators=[DataRequired()])
    observacoes = TextAreaField('Observações', validators=[Optional(), Length(max=500)])

class ConfiguracaoBotWhatsAppForm(FlaskForm):
    whatsapp_token = StringField('Token de Acesso do WhatsApp', 
                                 validators=[Optional(), Length(max=500)])
    whatsapp_phone_id = StringField('ID do Telefone', 
                                   validators=[Optional(), Length(max=100)])
    whatsapp_webhook_verify_token = StringField('Token de Verificação do Webhook', 
                                               validators=[Optional(), Length(max=200)])

class ConfiguracaoEmpresaForm(FlaskForm):
    nome_empresa = StringField('Nome da Empresa', 
                               validators=[DataRequired(), Length(min=2, max=200)])
    logo = FileField('Logo da Empresa', 
                     validators=[FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 
                                             'Apenas imagens são permitidas!')])

# Formulário para categorias de serviço
class CategoriaServicoForm(FlaskForm):
    nome = StringField('Nome da Categoria', validators=[DataRequired(), Length(min=2, max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])
    cor = StringField('Cor (Hexadecimal)', 
                     validators=[Optional(), 
                                Regexp(r'^#[0-9A-Fa-f]{6}$', 
                                      message='Cor deve estar no formato #RRGGBB')],
                     default='#007bff')
    ordem = IntegerField('Ordem de Exibição', 
                        validators=[Optional(), NumberRange(min=0)],
                        default=0)
    ativo = BooleanField('Ativo', default=True)

# Formulário para especialidades de funcionário
class EspecialidadeFuncionarioForm(FlaskForm):
    nome = StringField('Nome da Especialidade', validators=[DataRequired(), Length(min=2, max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])
    ativo = BooleanField('Ativo', default=True)

# Nova classe de formulário para serviços
class ServicoForm(FlaskForm):
    nome = StringField('Nome do Serviço', validators=[DataRequired(), Length(min=2, max=100)])
    descricao = TextAreaField('Descrição', validators=[Optional(), Length(max=500)])
    categoria_id = SelectField('Categoria', coerce=int, validators=[Optional()])
    
    # Preços e custos
    preco = FloatField('Preço (R$)', validators=[DataRequired(), NumberRange(min=0.01)])
    custo = FloatField('Custo (R$)', validators=[Optional(), NumberRange(min=0)], default=0.0)
    percentual_comissao = FloatField('Percentual de Comissão (%)', 
                                   validators=[Optional(), NumberRange(min=0, max=100)],
                                   default=0.0)
    
    # Duração e configurações
    duracao_minutos = IntegerField('Duração (minutos)', validators=[DataRequired(), NumberRange(min=1)])
    intervalo_entre_agendamentos = IntegerField('Intervalo entre Agendamentos (min)', 
                                              validators=[Optional(), NumberRange(min=0)],
                                              default=0)
    max_agendamentos_dia = IntegerField('Máx. Agendamentos por Dia', 
                                      validators=[Optional(), NumberRange(min=1)])
    antecedencia_minima_horas = IntegerField('Antecedência Mínima (horas)', 
                                           validators=[Optional(), NumberRange(min=0)],
                                           default=1)
    
    # Promoção
    preco_promocional = FloatField('Preço Promocional (R$)', 
                                 validators=[Optional(), NumberRange(min=0.01)])
    data_inicio_promocao = DateTimeField('Início da Promoção', 
                                       validators=[Optional()],
                                       widget=DateTimeInput())
    data_fim_promocao = DateTimeField('Fim da Promoção', 
                                     validators=[Optional()],
                                     widget=DateTimeInput())
    
    ordem = IntegerField('Ordem de Exibição', 
                        validators=[Optional(), NumberRange(min=0)],
                        default=0)
    ativo = BooleanField('Ativo', default=True)
    submit = SubmitField('Salvar Serviço')
    
    def __init__(self, *args, **kwargs):
        super(ServicoForm, self).__init__(*args, **kwargs)
        # Carregar categorias
        self.categoria_id.choices = [('', 'Sem Categoria')] + [
            (c.id, c.nome) for c in CategoriaServico.query.filter_by(ativo=True).order_by(CategoriaServico.ordem, CategoriaServico.nome).all()
        ]
    
    def validate_preco_promocional(self, field):
        """Validação para preço promocional"""
        if field.data and self.preco.data:
            if field.data >= self.preco.data:
                raise ValidationError('Preço promocional deve ser menor que o preço normal.')
    
    def validate_data_fim_promocao(self, field):
        """Validação para data fim da promoção"""
        if field.data and self.data_inicio_promocao.data:
            if field.data <= self.data_inicio_promocao.data:
                raise ValidationError('Data de fim deve ser posterior à data de início.')
    
    def validate_custo(self, field):
        """Validação para custo"""
        if field.data and self.preco.data:
            if field.data > self.preco.data:
                raise ValidationError('Custo não pode ser maior que o preço de venda.')