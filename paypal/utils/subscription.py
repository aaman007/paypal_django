import requests
from django.contrib.auth import get_user_model

from paypal.utils.base import PayPalHelper

User = get_user_model()


class PayPalSubscription(PayPalHelper):
    def get_subscription(self, subscription_id):
        # I-BW452GLLEP1G
        res = requests.get(
            url=f"{self.subscription_url}/{subscription_id}",
            headers=self.get_request_headers()
        )
        return res.json()

    def update_subscription(self):
        # If subscription update succeeds, it triggers the BILLING.SUBSCRIPTION.UPDATED webhook.
        """
        Can Update: subscriber.shipping_address, shipping_amount,
        billing_info.outstanding_balance, subscriber.payment_source
        """
        pass

    def cancel_subscription(self, subscription_id):
        # If subscription cancellation succeeds, it triggers the BILLING.SUBSCRIPTION.CANCELLED webhook.
        requests.post(
            url=f"{self.subscription_url}/{subscription_id}/cancel",
            headers=self.get_request_headers()
        )

    def activate_subscription(self, subscription_id):
        # If activate subscription succeeds, it triggers the BILLING.SUBSCRIPTION.ACTIVATED webhook.
        requests.post(
            url=f"{self.subscription_url}/{subscription_id}/activate",
            headers=self.get_request_headers()
        )

    def suspend_subscription(self, subscription_id):
        # If subscription suspension succeeds, it triggers the BILLING.SUBSCRIPTION.SUSPENDED webhook.
        requests.post(
            url=f"{self.subscription_url}/{subscription_id}/suspend",
            headers=self.get_request_headers()
        )

    def get_transactions(self, subscription_id):
        return requests.get(
            url=f"{self.subscription_url}/{subscription_id}/transactions",
            heeaders=self.get_request_headers()
        )
