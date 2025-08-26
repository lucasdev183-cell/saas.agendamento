from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from usuarios.models import Cargo, Servico
from configuracoes.models import ConfiguracaoEmpresa

User = get_user_model()


class Command(BaseCommand):
    help = 'Setup initial data for the application'

    def handle(self, *args, **options):
        self.stdout.write('Setting up initial data...')
        
        # Create master user
        if not User.objects.filter(username='master').exists():
            master_user = User.objects.create_user(
                username='master',
                email='master@jtsistemas.com',
                password='master123',
                nome='Administrador Master',
                tipo_usuario='master',
                ativo=True
            )
            self.stdout.write(
                self.style.SUCCESS(f'Created master user: master/master123')
            )
        else:
            self.stdout.write('Master user already exists')
        
        # Create default company configuration
        config, created = ConfiguracaoEmpresa.objects.get_or_create(
            id=1,
            defaults={
                'nome_empresa': 'JT Sistemas',
                'whatsapp_token': '',
                'whatsapp_phone_id': '',
                'whatsapp_webhook_verify_token': ''
            }
        )
        if created:
            self.stdout.write(
                self.style.SUCCESS('Created default company configuration')
            )
        else:
            self.stdout.write('Company configuration already exists')
        
        # Create default positions
        default_positions = [
            {'nome': 'Gerente', 'descricao': 'Gerente geral'},
            {'nome': 'Atendente', 'descricao': 'Atendimento ao cliente'},
            {'nome': 'Especialista', 'descricao': 'Especialista técnico'}
        ]
        
        for pos_data in default_positions:
            cargo, created = Cargo.objects.get_or_create(
                nome=pos_data['nome'],
                defaults={'descricao': pos_data['descricao']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created position: {pos_data["nome"]}')
                )
        
        # Create default services
        default_services = [
            {'nome': 'Corte de Cabelo', 'descricao': 'Corte masculino/feminino', 'preco': 25.00, 'duracao_minutos': 30},
            {'nome': 'Manicure', 'descricao': 'Cuidados com as unhas das mãos', 'preco': 15.00, 'duracao_minutos': 45},
            {'nome': 'Pedicure', 'descricao': 'Cuidados com as unhas dos pés', 'preco': 20.00, 'duracao_minutos': 60},
        ]
        
        for service_data in default_services:
            servico, created = Servico.objects.get_or_create(
                nome=service_data['nome'],
                defaults={
                    'descricao': service_data['descricao'],
                    'preco': service_data['preco'],
                    'duracao_minutos': service_data['duracao_minutos'],
                    'ativo': True
                }
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'Created service: {service_data["nome"]}')
                )
        
        self.stdout.write(
            self.style.SUCCESS('Initial data setup completed successfully!')
        )