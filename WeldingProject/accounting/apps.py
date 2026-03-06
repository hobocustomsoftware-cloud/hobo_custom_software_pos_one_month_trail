from django.apps import AppConfig


class AccountingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounting'
    verbose_name = 'စာရင်းကိုင် & P&L'
    
    def ready(self):
        """Register signals when app is ready"""
        import accounting.signals  # noqa
