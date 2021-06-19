from django.contrib import admin

from paypal.models import (
    Product,
    BillingPlan,
    Frequency,
    PricingScheme,
    BillingCycle,
    PaymentPreference,
    Amount,
    Subscription,
    PayPalProfile
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    search_fields = ['product_id', 'name']
    list_display = ['name', 'product_id', 'description', 'type', 'category']
    list_filter = ['type', 'category']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['product_id', 'type', 'create_time', 'update_time', 'links']
        return ['product_id', 'create_time', 'update_time', 'links']


@admin.register(Amount)
class AmountAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['currency_code', 'value']
        return []


@admin.register(Frequency)
class FrequencyAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['interval_unit', 'interval_count']
        return []


@admin.register(PricingScheme)
class PricingSchemeAdmin(admin.ModelAdmin):
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['fixed_price']
        return []


class BillingCycleInline(admin.StackedInline):
    model = BillingCycle
    min_num = 1
    extra = 0
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['frequency', 'tenure_type', 'sequence', 'total_cycles']
        return []

    def get_max_num(self, request, obj=None, **kwargs):
        if obj:
            return obj.billing_cycles.count()


class PaymentPreferenceInline(admin.StackedInline):
    model = PaymentPreference
    min_num = 1
    can_delete = False

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ['setup_fee', 'setup_fee_failure_action']
        return []


@admin.register(BillingPlan)
class BillingPlanAdmin(admin.ModelAdmin):
    list_filter = ['status']
    list_display = ['name', 'plan_id', 'product', 'status']
    actions = ['activate', 'deactivate']
    inlines = [BillingCycleInline, PaymentPreferenceInline]

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                'name', 'status', 'plan_id', 'product', 'quantity_supported', 'create_time', 'update_time',
                'links'
            ]
        return ['plan_id', 'quantity_supported', 'create_time', 'update_time', 'links']

    def activate(self, request, queryset):
        from paypal.utils.billing_plan import PayPalBillingPlan
        paypal_helper = PayPalBillingPlan()
        for plan in queryset:
            paypal_helper.activate_billing_plan(plan.plan_id)
        queryset.update(status='ACTIVE')

    def deactivate(self, request, queryset):
        from paypal.utils.billing_plan import PayPalBillingPlan
        paypal_helper = PayPalBillingPlan()
        for plan in queryset:
            paypal_helper.deactivate_billing_plan(plan.plan_id)
        queryset.update(status='INACTIVE')

    activate.short_description = 'Activate selected plans'
    deactivate.short_description = 'Deactivate selected plans'


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_filter = ['status', 'shipping_amount']
    list_display = ['user', 'plan', 'subscription_id', 'status', 'shipping_amount']
    readonly_fields = [
        'user', 'plan', 'subscription_id', 'status', 'start_time', 'create_time', 'update_time',
        'billing_info', 'links', 'shipping_amount'
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(PayPalProfile)
class PayPalProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'subscription_valid_till', 'has_subscription']

    def has_subscription(self, obj: PayPalProfile):
        return obj.has_subscription

    has_subscription.boolean = True
