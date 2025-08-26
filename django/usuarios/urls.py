from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    # Authentication
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # Users management
    path('cadastro/usuarios/pesquisar/', views.usuarios_pesquisar, name='usuarios_pesquisar'),
    path('cadastro/usuario/inserir/', views.usuario_inserir, name='usuario_inserir'),
    path('cadastro/usuario/visualizar/<int:usuario_id>/', views.usuario_visualizar, name='usuario_visualizar'),
    path('cadastro/usuario/editar/<int:usuario_id>/', views.usuario_editar, name='usuario_editar'),
    
    # Clients management
    path('cadastro/clientes/pesquisar/', views.clientes_pesquisar, name='clientes_pesquisar'),
    path('cadastro/clientes/inserir/', views.cliente_inserir, name='cliente_inserir'),
    
    # Employees management
    path('funcionarios/', views.funcionarios, name='funcionarios'),
    path('funcionarios/criar/', views.funcionario_criar, name='funcionario_criar'),
    
    # Positions management
    path('cargos/', views.cargos_main, name='cargos_main'),
    path('cargos/inserir/', views.cargo_inserir, name='cargo_inserir'),
    
    # Services management
    path('servicos/', views.servicos_main, name='servicos_main'),
    path('servicos/inserir/', views.servico_inserir, name='servico_inserir'),
]