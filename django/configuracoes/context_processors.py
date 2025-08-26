from .models import ConfiguracaoEmpresa


def empresa_config(request):
    """Context processor to make company configuration available in all templates"""
    try:
        config = ConfiguracaoEmpresa.objects.first()
        return {'empresa_config': config}
    except ConfiguracaoEmpresa.DoesNotExist:
        return {'empresa_config': None}