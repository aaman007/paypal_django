from django.apps import AppConfig


class PaypalConfig(AppConfig):
    name = 'paypal'

    def ready(self):
        import paypal.signals
