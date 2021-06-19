from django.conf import settings
from django.core.exceptions import ImproperlyConfigured

if not hasattr(settings, 'PAYPAL_ENVIRONMENT') or settings.PAYPAL_ENVIRONMENT not in ["SANDBOX", "PRODUCTION"]:
    raise ImproperlyConfigured(
        "PAYPAL_ENVIRONMENT is not configured properly in settings, set it to 'SANDBOX' or 'PRODUCTION'"
    )

if not hasattr(settings, 'PAYPAL_CLIENT_ID'):
    raise ImproperlyConfigured("PAYPAL_CLIENT_ID is not configured properly in settings")

if not hasattr(settings, 'PAYPAL_SECRET_KEY'):
    raise ImproperlyConfigured("PAYPAL_SECRET_KEY is not configured properly in settings")
