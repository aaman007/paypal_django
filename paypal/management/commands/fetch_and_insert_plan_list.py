from django.core.management.base import BaseCommand
from django.db.models import signals

from paypal.models import BillingPlan, Amount, Frequency, BillingCycle, PaymentPreference, PricingScheme, Product
from paypal.signals import update_plan, create_plan, update_pricing
from paypal.utils.billing_plan import PayPalBillingPlan


class Command(BaseCommand):
    help = 'Fetches and Inserts PayPal product list'

    def _print_exception(self, e: Exception, prefix: str = None):
        prefix = f'{prefix} | ' if prefix else ''
        self.stdout.write(self.style.ERROR(f"{prefix}{type(e).__name__} | {e}"))

    @staticmethod
    def disconnect_signals():
        signals.post_save.disconnect(create_plan, BillingPlan)
        signals.post_save.disconnect(update_pricing, BillingPlan)
        signals.pre_save.disconnect(update_plan, BillingPlan)

    @staticmethod
    def reconnect_signals():
        signals.post_save.connect(create_plan, BillingPlan)
        signals.post_save.connect(update_pricing, BillingPlan)
        signals.pre_save.connect(update_plan, BillingPlan)

    def handle(self, *args, **options):
        paypal_helper = PayPalBillingPlan()
        paypal_plans = paypal_helper.get_billing_plans()
        count = 0

        for plan in paypal_plans:
            if not BillingPlan.objects.filter(plan_id=plan.get('id')).exists():
                plan = paypal_helper.get_billing_plan(plan.get('id'))
                count += 1
                billing_cycles = plan.get("billing_cycles")
                preferences = plan.get("payment_preferences")

                product = Product.objects.get(product_id=plan.get("product_id"))

                self.disconnect_signals()
                billing_plan = BillingPlan.objects.create(
                    product=product,
                    plan_id=plan.get("id"),
                    name=plan.get("name"),
                    description=plan.get("description"),
                    status=plan.get("status"),
                    create_time=plan.get("create_time"),
                    update_time=plan.get("update_time"),
                    quantity_supported=plan.get("quantity_supported", False),
                    links=plan.get("links")
                )
                self.reconnect_signals()

                setup_fee, _ = Amount.objects.get_or_create(
                    value=preferences["setup_fee"]["value"],
                    currency_code=preferences["setup_fee"]["currency_code"],
                )

                PaymentPreference.objects.create(
                    billing_plan=billing_plan,
                    auto_bill_outstanding=preferences.get("auto_bill_outstanding"),
                    setup_fee_failure_action=preferences.get("setup_fee_failure_action"),
                    payment_failure_threshold=preferences.get("payment_failure_threshold"),
                    setup_fee=setup_fee
                )

                for cycle in billing_cycles:
                    frequency, _ = Frequency.objects.get_or_create(
                        interval_unit=cycle["frequency"]["interval_unit"],
                        interval_count=cycle["frequency"]["interval_count"]
                    )

                    if cycle.get("pricing_scheme"):
                        fixed_price, _ = Amount.objects.get_or_create(
                            value=cycle["pricing_scheme"]["fixed_price"]["value"],
                            currency_code=cycle["pricing_scheme"]["fixed_price"]["currency_code"],
                        )
                        pricing_scheme, _ = PricingScheme.objects.get_or_create(fixed_price=fixed_price)
                    else:
                        pricing_scheme = None
                    BillingCycle.objects.create(
                        billing_plan=billing_plan,
                        frequency=frequency,
                        tenure_type=cycle.get('tenure_type'),
                        sequence=cycle.get('sequence'),
                        total_cycles=cycle.get('total_cycles'),
                        pricing_scheme=pricing_scheme
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f"Fetched {len(paypal_plans)} plans and inserted {count} plans successfully"
            )
        )
