#!/bin/bash

echo "🚀 Fazendo commit da versão Django do sistema..."

# Adicionar todos os arquivos da pasta django
git add django/

# Verificar o que será commitado
echo "📁 Arquivos que serão commitados:"
git status --porcelain django/

# Fazer o commit
git commit -m "feat: Add Django version of scheduling system

- Convert Flask application to Django framework
- Maintain all original functionalities and layout
- Add comprehensive Django project structure:
  * usuarios app (user management, clients, employees)
  * agendamentos app (appointments and scheduling)
  * configuracoes app (company settings, WhatsApp bot)
- Implement Django models, views, forms, and templates
- Add responsive Bootstrap 5 interface
- Include management commands for initial data setup
- Add comprehensive documentation and setup instructions

Features:
✅ User authentication and authorization
✅ Master and restricted user types
✅ Client management (passwordless)
✅ Employee and position management
✅ Service management with pricing
✅ Appointment scheduling system
✅ Dashboard with statistics
✅ Company configuration and logo upload
✅ WhatsApp bot configuration
✅ Reports and analytics
✅ Responsive design
✅ PostgreSQL/SQLite support

Login credentials:
- User: master
- Password: master123"

# Push para o GitHub
echo "⬆️  Fazendo push para o GitHub..."
git push origin main

echo "✅ Commit realizado com sucesso!"
echo "🌐 Verifique seu repositório no GitHub para ver a nova pasta 'django'"