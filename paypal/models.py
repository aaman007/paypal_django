from datetime import datetime

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class AbstractTimestampModel(models.Model):
    created_date = models.DateTimeField(auto_now_add=True)
    modified_date = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Product(AbstractTimestampModel):
    # https://developer.paypal.com/docs/api/catalog-products/v1/#products_create

    class ProductType(models.TextChoices):
        PHYSICAL = 'PHYSICAL', _('Physical Goods')
        DIGITAL = 'DIGITAL', _('Digital Goods')
        SERVICE = 'SERVICE', _('A Service')

    class ProductCategory(models.TextChoices):
        SOFTWARE = 'SOFTWARE', _('Software')

    product_id = models.CharField(verbose_name=_('Product ID'), max_length=50, unique=True)
    name = models.CharField(verbose_name=_('Name'), max_length=127)
    description = models.CharField(verbose_name=_('Description'), max_length=256)
    type = models.CharField(verbose_name=_('Type'), max_length=24, choices=ProductType.choices)
    category = models.CharField(verbose_name=_('Category'), max_length=60, choices=ProductCategory.choices)
    image_url = models.URLField(verbose_name=_('Image URL'), blank=True)
    home_url = models.URLField(verbose_name=_('Home URL'), blank=True)

    create_time = models.DateTimeField(verbose_name=_('Create Time'))
    update_time = models.DateTimeField(verbose_name=_('Update Time'))
    links = models.JSONField(verbose_name=_('Links'), default=list, blank=True)

    class Meta:
        ordering = ['-id']
        verbose_name = _('Product')
        verbose_name_plural = _('Products')

    def __str__(self):
        return self.name


class BillingPlan(AbstractTimestampModel):
    # https://developer.paypal.com/docs/subscriptions/full-integration/plan-management/

    class BillingPlanStatus(models.TextChoices):
        CREATED = 'CREATED', _('Created')
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')

    plan_id = models.CharField(verbose_name=_('Billing Plan ID'), max_length=128, blank=True)
    product = models.ForeignKey(
        verbose_name=_('Product'),
        to='Product',
        related_name='plans',
        on_delete=models.CASCADE,
        null=True
    )
    name = models.CharField(verbose_name=_('Name'), max_length=128)
    description = models.CharField(verbose_name=_('Description'), max_length=127)
    status = models.CharField(
        verbose_name=_('Status'),
        max_length=20,
        choices=BillingPlanStatus.choices,
        default='ACTIVE'
    )

    quantity_supported = models.BooleanField(verbose_name=_('Quantity Supported'), default=False)
    create_time = models.DateTimeField(verbose_name=_('Create Time'), null=True)
    update_time = models.DateTimeField(verbose_name=_('Update Time'), null=True)
    links = models.JSONField(verbose_name=_('Links'), default=list, blank=True)

    class Meta:
        ordering = ['-id']
        verbose_name = _('Billing Plan')
        verbose_name_plural = _('Billing Plans')

    def __str__(self):
        return self.name

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        if self.id:
            self.old_instance = self.__class__.objects.get(id=self.id)
        return super().save(force_insert, force_update, using, update_fields)


class Amount(models.Model):
    currency_code = models.CharField(verbose_name=_('Currency Code'), max_length=40)
    value = models.FloatField(verbose_name=_('Value'))

    class Meta:
        ordering = ['-id']
        verbose_name = _('Amount')
        verbose_name_plural = _('Amounts')

    def __str__(self):
        return f"{self.currency_code} {self.value}"


class Frequency(models.Model):
    class IntervalUnit(models.TextChoices):
        MONTH = 'MONTH', _('Month')

    interval_unit = models.CharField(verbose_name=_('Interval Unit'), max_length=20, choices=IntervalUnit.choices)
    interval_count = models.PositiveIntegerField(verbose_name=_('Interval Count'), default=1)

    class Meta:
        ordering = ['-id']
        verbose_name = _('Frequency')
        verbose_name_plural = _('Frequencies')

    def __str__(self):
        return f"{self.interval_count} ({self.interval_unit})"


class PricingScheme(models.Model):
    fixed_price = models.ForeignKey(
        verbose_name=_('Fixed Price'),
        to='Amount',
        related_name='pricing_schemes',
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ['-id']
        verbose_name = _('Pricing Scheme')
        verbose_name_plural = _('Pricing Schemes')

    def __str__(self):
        return self.fixed_price.__str__()


class BillingCycle(models.Model):
    class TenureType(models.TextChoices):
        TRIAL = 'TRIAL', _('Trial')
        REGULAR = 'REGULAR', _('Regular')

    billing_plan = models.ForeignKey(
        verbose_name=_('Billing Plan'),
        to='BillingPlan',
        related_name='billing_cycles',
        on_delete=models.CASCADE
    )
    frequency = models.ForeignKey(
        verbose_name=_('Frequency'),
        to='Frequency',
        related_name='billing_cycles',
        on_delete=models.CASCADE
    )
    tenure_type = models.CharField(verbose_name=_('Tenure Type'), max_length=20, choices=TenureType.choices)
    sequence = models.PositiveIntegerField(verbose_name=_('Sequence'), default=1)
    total_cycles = models.PositiveIntegerField(verbose_name=_('Total Cycles'), default=0)
    pricing_scheme = models.ForeignKey(
        verbose_name=_('Pricing Scheme'),
        to='PricingScheme',
        related_name='billing_cycles',
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    class Meta:
        ordering = ['-id']
        verbose_name = _('Billing Cycle')
        verbose_name_plural = _('Billing Cycles')

    def __str__(self):
        return f"{self.tenure_type} ({self.frequency})"


class PaymentPreference(models.Model):
    class SetupFeeFailureAction(models.TextChoices):
        CONTINUE = 'CONTINUE', _('Continue')

    billing_plan = models.OneToOneField(
        verbose_name=_('Billing Plan'),
        to='BillingPlan',
        related_name='payment_preferences',
        on_delete=models.CASCADE
    )
    auto_bill_outstanding = models.BooleanField(verbose_name=_('Auto Bill Outstanding'), default=True)
    setup_fee = models.ForeignKey(
        verbose_name=_('Setup Fee'),
        to='Amount',
        related_name='payment_preferences',
        on_delete=models.CASCADE
    )
    setup_fee_failure_action = models.CharField(
        verbose_name=_('Setup Fee Failure Action'),
        max_length=30,
        choices=SetupFeeFailureAction.choices
    )
    payment_failure_threshold = models.PositiveIntegerField(verbose_name=_('Payment Failure Threshold'), default=0)

    class Meta:
        ordering = ['-id']
        verbose_name = _('Payment Preference')
        verbose_name_plural = _('Payment Preferences')


class Subscription(models.Model):
    # https://developer.paypal.com/docs/subscriptions/full-integration/

    class SubscriptionStatus(models.TextChoices):
        ACTIVE = 'ACTIVE', _('Active')
        INACTIVE = 'INACTIVE', _('Inactive')
        SUSPENDED = 'SUSPENDED', _('Suspended')

    user = models.ForeignKey(
        verbose_name=_('User'),
        to=User,
        related_name='paypal_subscriptions',
        on_delete=models.CASCADE
    )
    plan = models.ForeignKey(
        verbose_name=_('Plan'),
        to='BillingPlan',
        related_name='subscriptions',
        on_delete=models.CASCADE
    )

    subscription_id = models.CharField(verbose_name=_('Subscription Id'), max_length=160)
    status = models.CharField(verbose_name=_('Status'), max_length=40, choices=SubscriptionStatus.choices)
    start_time = models.DateTimeField(verbose_name=_('Start Time'))
    shipping_amount = models.ForeignKey(
        verbose_name=_('Shipping Amount'),
        to='Amount',
        on_delete=models.CASCADE
    )
    billing_info = models.JSONField(verbose_name=_('Billing Info'), default=dict, blank=True)
    create_time = models.DateTimeField(verbose_name=_('Create Time'))
    update_time = models.DateTimeField(verbose_name=_('Update Time'))
    links = models.JSONField(verbose_name=_('Links'), default=list)


class Subscriber(models.Model):
    name = models.JSONField(verbose_name=_('Name'), default=dict)
    email = models.EmailField(verbose_name=_('Email'))
    subscription = models.OneToOneField(
        verbose_name=_('Subscription'),
        to='Subscription',
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.email


class PayPalProfile(AbstractTimestampModel):
    user = models.OneToOneField(
        verbose_name=_('User'),
        to=User,
        related_name='paypal_profile',
        on_delete=models.CASCADE
    )

    subscription_valid_till = models.DateTimeField(
        verbose_name=_('Subscription Valid Till'),
        blank=True,
        null=True
    )

    class Meta:
        ordering = ['-id']
        verbose_name = _('Paypal Profile')
        verbose_name_plural = _('Paypal Profiles')

    def __str__(self):
        return self.user.username

    @property
    def has_subscription(self) -> bool:
        if not self.subscription_valid_till:
            return False
        return self.subscription_valid_till <= timezone.now()

    def update_validity(self, dt: datetime):
        self.subscription_valid_till = dt
        self.save(update_fields=['subscription_valid_till', 'modified_date'])
        self.refresh_from_db()

