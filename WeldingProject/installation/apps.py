from django.apps import AppConfig


class InstallationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'installation'
    verbose_name = 'တပ်ဆင်မှု (Installation)'

    def ready(self):
        """Register signals when app is ready"""
        import installation.signals  # noqa
