from django.db.models.signals import pre_save, post_save
from django.db import transaction
from django.dispatch import receiver

from paypal.models import Product, BillingPlan, PaymentPreference
from paypal.utils.product import PayPalProduct
from paypal.utils.billing_plan import PayPalBillingPlan


@receiver(pre_save, sender=Product)
def update_product(sender, instance: Product, **kwargs):
    created = instance.id is None
    if not created:
        old_instance = Product.objects.get(id=instance.id)
        has_changed = False
        paths = {}

        for field in ['name', 'description', 'category', 'image_url', 'home_url']:
            if getattr(instance, field) != getattr(old_instance, field):
                has_changed = True
                paths.update({
                    f"/{field}": getattr(instance, field)
                })

        if has_changed:
            PayPalProduct().update_product(instance.product_id, paths)
            product = PayPalProduct().get_product(instance.product_id)
            instance.update_time = product.get('update_time')


@receiver(pre_save, sender=Product)
def create_product(sender, instance: Product, **kwargs):
    created = instance.id is None
    if created:
        data = {
            "name": instance.name,
            "description": instance.description,
            "type": instance.type,
            "category": instance.category
        }
        if instance.image_url:
            data.update({"image_url": instance.image_url})
        if instance.home_url:
            data.update({"home_url": instance.home_url})

        product = PayPalProduct().create_product(data)
        instance.product_id = product.get("id")
        instance.create_time = product.get('create_time')
        instance.update_time = product.get('create_time')
        instance.links = product.get('links')


@receiver(pre_save, sender=BillingPlan)
def update_plan(sender, instance: BillingPlan, **kwargs):
    created = instance.id is None
    if not created:
        old_instance = BillingPlan.objects.get(id=instance.id)
        paypal_helper = PayPalBillingPlan()
        has_changed = False
        paths = dict()

        fields = [
            'description',
            'auto_bill_outstanding',
            'payment_failure_threshold'
        ]
        for field in fields[:1]:
            if getattr(old_instance, field) != getattr(instance, field):
                paths[f"/{field}"] = getattr(instance, field)
                has_changed = True
        for field in fields[1:3]:
            if getattr(old_instance.payment_preferences, field) != getattr(instance.payment_preferences, field):
                paths[f"/payment_preferences/{field}"] = getattr(instance.payment_preferences, field)
                has_changed = True

        if has_changed:
            paypal_helper.update_billing_plan(instance.plan_id, paths)
            plan = paypal_helper.get_billing_plan(instance.plan_id)
            instance.update_time = plan.get('update_time')


def create_billing_plan(instance):
    billing_cycles = []

    for cycle in instance.billing_cycles.all():
        billing_cycles.append({
            "frequency": {
                "interval_unit": cycle.frequency.interval_unit,
                "interval_count": cycle.frequency.interval_count
            },
            "tenure_type": cycle.tenure_type,
            "sequence": cycle.sequence,
            "total_cycles": cycle.total_cycles,
            "pricing_scheme": {
                "fixed_price": {
                    "value": cycle.pricing_scheme.fixed_price.value,
                    "currency_code": cycle.pricing_scheme.fixed_price.currency_code
                }
            }
        })
    data = {
        "product_id": instance.product.product_id,
        "name": instance.name,
        "description": instance.description,
        "billing_cycles": billing_cycles,
        "payment_preferences": {
            "auto_bill_outstanding": instance.payment_preferences.auto_bill_outstanding,
            "setup_fee": {
                "value": instance.payment_preferences.setup_fee.value,
                "currency_code": instance.payment_preferences.setup_fee.currency_code
            },
            "setup_fee_failure_action": instance.payment_preferences.setup_fee_failure_action,
            "payment_failure_threshold": instance.payment_preferences.payment_failure_threshold
        }
    }
    plan = PayPalBillingPlan().create_billing_plan(data)
    BillingPlan.objects.filter(id=instance.id).update(
        plan_id=plan.get('id'),
        quantity_supported=plan.get('quantity_supported', False),
        create_time=plan.get('create_time'),
        update_time=plan.get('create_time'),
        links=plan.get('links')
    )


@receiver(post_save, sender=BillingPlan)
def create_plan(sender, instance: BillingPlan, created, **kwargs):
    if created:
        transaction.on_commit(lambda: create_billing_plan(instance))


def update_billing_plan_pricing(instance, old_schemes, cycles):
    pricing_schemes = []

    for cycle in cycles:
        if cycle.pricing_scheme not in old_schemes:
            pricing_schemes.append({
                "billing_cycle_sequence": cycle.sequence,
                "pricing_scheme": {
                    "fixed_price": {
                        "value": cycle.pricing_scheme.fixed_price.value,
                        "currency_code": cycle.pricing_scheme.fixed_price.currency_code
                    }
                }
            })

    if pricing_schemes:
        paypal_helper = PayPalBillingPlan()
        paypal_helper.update_pricing(
            instance.plan_id, {
                "pricing_schemes": pricing_schemes
            }
        )
        plan = paypal_helper.get_billing_plan(instance.plan_id)
        BillingPlan.objects.filter(id=instance.id).update(
            update_time=plan.get('update_time')
        )


@receiver(post_save, sender=BillingPlan)
def update_pricing(sender, instance: BillingPlan, created, **kwargs):
    if not created:
        old_instance = getattr(instance, 'old_instance')
        old_schemes = [cycle.pricing_scheme for cycle in old_instance.billing_cycles.all()]
        cycles = instance.billing_cycles.all()
        transaction.on_commit(lambda: update_billing_plan_pricing(instance, old_schemes, cycles))
