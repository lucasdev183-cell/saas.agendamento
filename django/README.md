# Sistema de Agendamento - Django

Este é um sistema completo de agendamento desenvolvido em Django, convertido do sistema original em Flask. O sistema oferece funcionalidades para gerenciamento de usuários, clientes, funcionários, serviços e agendamentos.

## Funcionalidades

### 🔐 Autenticação e Autorização
- Sistema de login seguro
- Usuários Master e Restritos
- Controle de permissões granular

### 👥 Gerenciamento de Usuários
- Cadastro de usuários do sistema
- Cadastro de clientes (sem senha)
- Gerenciamento de funcionários
- Diferentes níveis de acesso

### 📅 Sistema de Agendamentos
- Criação de agendamentos
- Controle de status (Agendado, Concluído, Cancelado)
- Visualização por tipo de usuário
- Relatórios de agendamentos

### 🏢 Configurações da Empresa
- Configuração de dados da empresa
- Upload de logo
- Configurações do Bot WhatsApp

### 📊 Dashboard Intuitivo
- Estatísticas em tempo real
- Agendamentos recentes
- Ações rápidas
- Interface responsiva

## Tecnologias Utilizadas

- **Django 5.2.5** - Framework web
- **PostgreSQL** - Banco de dados (SQLite para desenvolvimento)
- **Bootstrap 5** - Framework CSS
- **Font Awesome** - Ícones
- **Django Crispy Forms** - Formulários estilizados

## Instalação e Configuração

### Pré-requisitos
- Python 3.11+
- pip (gerenciador de pacotes Python)
- Banco de dados PostgreSQL (para produção)

### 1. Configuração do Ambiente

```bash
# Clone ou navegue até o diretório do projeto
cd django

# Crie um ambiente virtual
python -m venv venv

# Ative o ambiente virtual
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### 2. Configuração do Banco de Dados

#### Para Desenvolvimento (SQLite):
O projeto está configurado para usar SQLite por padrão.

#### Para Produção (PostgreSQL):
1. Descomente as configurações do PostgreSQL no `settings.py`
2. Configure as variáveis de ambiente:
   ```bash
   export PGDATABASE=db_sa
   export PGUSER=postgres
   export PGPASSWORD=sua_senha
   export PGHOST=localhost
   export PGPORT=5432
   ```

### 3. Configuração Inicial

```bash
# Execute as migrações
python manage.py migrate

# Configure dados iniciais
python manage.py setup_initial_data

# (Opcional) Crie um superusuário para o Django Admin
python manage.py createsuperuser
```

### 4. Executar o Servidor

```bash
# Servidor de desenvolvimento
python manage.py runserver

# O sistema estará disponível em: http://localhost:8000
```

## Acesso ao Sistema

### Usuário Master Padrão
- **Usuário:** master
- **Senha:** master123

Este usuário tem acesso completo a todas as funcionalidades do sistema.

## Estrutura do Projeto

```
django/
├── saas_agendamento/          # Configurações do projeto
│   ├── settings.py            # Configurações principais
│   ├── urls.py               # URLs principais
│   └── wsgi.py               # Configuração WSGI
├── usuarios/                  # App de usuários
│   ├── models.py             # Modelos de usuário, cargo, etc.
│   ├── views.py              # Views do sistema
│   ├── forms.py              # Formulários
│   └── urls.py               # URLs dos usuários
├── agendamentos/             # App de agendamentos
│   ├── models.py             # Modelo de agendamento
│   ├── views.py              # Views de agendamentos
│   └── forms.py              # Formulários de agendamento
├── configuracoes/            # App de configurações
│   ├── models.py             # Configurações da empresa
│   ├── views.py              # Views de configuração
│   └── context_processors.py # Processador de contexto
├── templates/                # Templates HTML
│   ├── base.html             # Template base
│   ├── usuarios/             # Templates de usuários
│   └── agendamentos/         # Templates de agendamentos
├── static/                   # Arquivos estáticos
│   ├── css/                  # Arquivos CSS
│   └── js/                   # Arquivos JavaScript
└── requirements.txt          # Dependências do projeto
```

## Funcionalidades por Tipo de Usuário

### 👑 Master
- Acesso completo ao sistema
- Gerenciamento de usuários
- Configurações da empresa
- Relatórios completos
- Configuração do Bot WhatsApp

### 👤 Usuário Restrito
- Acesso baseado em permissões configuradas
- Pode ter permissões para:
  - Cadastrar clientes
  - Cadastrar funcionários
  - Gerenciar cargos
  - Criar agendamentos
  - Visualizar agendamentos
  - Acessar relatórios

### 👨‍💼 Funcionário
- Visualiza apenas seus próprios agendamentos
- Pode atualizar status dos agendamentos
- Dashboard personalizado

### 👤 Cliente
- Visualiza apenas seus próprios agendamentos
- Não possui acesso administrativo

## Configuração para Produção

### 1. Configurações de Segurança
```python
# Em settings.py para produção:
DEBUG = False
ALLOWED_HOSTS = ['seu-dominio.com']
SECRET_KEY = 'chave-secreta-forte'
```

### 2. Servidor Web
```bash
# Usando Gunicorn
gunicorn saas_agendamento.wsgi:application

# Ou configurar com nginx + gunicorn
```

### 3. Arquivos Estáticos
```bash
# Coletar arquivos estáticos
python manage.py collectstatic
```

## Personalização

### Alterando o Nome da Empresa
1. Acesse as configurações do sistema como usuário Master
2. Vá em "Configurações" > "Configurações da Empresa"
3. Altere o nome e faça upload do logo

### Adicionando Novos Serviços
1. Acesse "Cadastro" > "Serviços"
2. Clique em "Inserir Serviço"
3. Preencha os dados (nome, descrição, preço, duração)

### Configurando Permissões
1. No cadastro de usuários, configure as permissões específicas
2. Cada usuário restrito pode ter permissões individuais

## Troubleshooting

### Problemas Comuns

1. **Erro de banco de dados**
   - Verifique se as configurações do banco estão corretas
   - Execute `python manage.py migrate`

2. **Arquivos estáticos não carregam**
   - Execute `python manage.py collectstatic`
   - Verifique as configurações de STATIC_URL

3. **Erro de permissão**
   - Verifique se o usuário tem as permissões necessárias
   - Teste com usuário Master

## Suporte

Para suporte ou dúvidas sobre o sistema:
- Verifique a documentação do Django: https://docs.djangoproject.com/
- Analise os logs de erro para mais informações
- Teste com dados de exemplo usando o comando `setup_initial_data`

## Licença

Este sistema foi desenvolvido para fins educacionais e comerciais. 

---

**JT Sistemas** - Sistema de Agendamento Profissional