from django.views.generic import View, TemplateView

from paypal.models import BillingPlan


class SubscribeTemplateView(TemplateView):
    template_name = 'paypal/subscribe.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            "plan_id": BillingPlan.objects.first().plan_id
        })
        return context
