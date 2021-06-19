import requests
from django.conf import settings
from paypalcheckoutsdk.core import SandboxEnvironment, LiveEnvironment, PayPalHttpClient


class PayPalHelper:
    def __init__(self):
        self.client_id = settings.PAYPAL_CLIENT_ID
        self.secret_key = settings.PAYPAL_SECRET_KEY

        if settings.PAYPAL_ENVIRONMENT == "PRODUCTION":
            self.base_url = "https://api-m.paypal.com"
            self.environment = LiveEnvironment(client_id=self.client_id, client_secret=self.secret_key)
        else:
            self.base_url = "https://api-m.sandbox.paypal.com"
            self.environment = SandboxEnvironment(client_id=self.client_id, client_secret=self.secret_key)

        self.client = PayPalHttpClient(environment=self.environment)
        self.access_token = None

        self.access_token_url = f"{self.base_url}/v1/oauth2/token"
        self.products_url = f"{self.base_url}/v1/catalogs/products"
        self.plan_url = f"{self.base_url}/v1/billing/plans"
        self.subscription_url = f"{self.base_url}/v1/billing/subscriptions"

    def get_access_token(self):
        if self.access_token:
            return self.access_token

        self.access_token = requests.post(
            self.access_token_url,
            auth=(self.client_id, self.secret_key),
            data={
                "grant_type": "client_credentials"
            },
            headers={
                "Accept": "application/json",
                "Accept-Language": "en_US"
            },
        ).json().get('access_token')

        return self.access_token

    def get_request_headers(self):
        return {
            "Accept": "application/json",
            "Accept-Language": "en_US",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.get_access_token()}"
        }
