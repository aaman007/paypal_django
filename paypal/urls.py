from django.urls import path, include

from paypal.views import SubscribeTemplateView

app_name = 'paypal'

urlpatterns = [
    path('webhook/', include('paypal.webhook.urls')),
    path('subscribe/', SubscribeTemplateView.as_view(), name='subscribe')
]
