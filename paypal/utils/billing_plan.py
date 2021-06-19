import requests

from paypal.utils.base import PayPalHelper


class PayPalBillingPlan(PayPalHelper):
    def get_billing_plans(self):
        return requests.get(
            self.plan_url,
            headers=self.get_request_headers()
        ).json().get('plans', [])

    def get_billing_plan(self, plan_id):
        return requests.get(
            f"{self.plan_url}/{plan_id}",
            headers=self.get_request_headers()
        ).json()

    def create_billing_plan(self, data):
        # If creating a plan succeeds, it triggers the BILLING.PLAN.CREATED webhook
        return requests.post(
            self.plan_url,
            headers=self.get_request_headers(),
            json=data
        ).json()

    def update_billing_plan(self, plan_id, paths: dict):
        # If the update succeeds, it triggers the BILLING.PLAN.UPDATED webhook.
        """
        Can update these fields [description, auto_bill_outstanding, payment_failure_threshold]
        Example: update_billing_plan.json file
        """
        data: list = list()
        for path, value in paths.items():
            data.append({
                "op": "replace",
                "path": path,
                "value": value
            })
        requests.patch(
            f"{self.plan_url}/{plan_id}",
            headers=self.get_request_headers(),
            json=data
        )

    def update_pricing(self, plan_id, data):
        # BILLING.PLAN.PRICING.CHANGE.ACTIVATED
        """
        Example: update_plan_pricing.json
        """
        requests.post(
            f"{self.plan_url}/{plan_id}/update-pricing-schemes",
            headers=self.get_request_headers(),
            json=data
        )

    def activate_billing_plan(self, plan_id):
        # If the plan activation succeeds, it triggers the BILLING.PLAN.ACTIVATED webhook.
        requests.post(
            f"{self.plan_url}/{plan_id}/activate",
            headers=self.get_request_headers(),
        )

    def deactivate_billing_plan(self, plan_id):
        # If deactivation succeeds, it triggers the BILLING.PLAN.DEACTIVATED webhook.
        requests.post(
            f"{self.plan_url}/{plan_id}/deactivate",
            headers=self.get_request_headers(),
        )
