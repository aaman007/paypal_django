from paypalcheckoutsdk.orders import OrdersCaptureRequest, OrdersCreateRequest

from paypal.utils.base import PayPalHelper


class PayPalOrder(PayPalHelper):
    def create_order(self, price):
        create_order = OrdersCreateRequest()

        create_order.request_body({
            "intent": "CAPTURE",
            "purchase_units": [
                {
                    "amount": {
                        "currency_code": "USD",
                        "value": price,
                        "breakdown": {
                            "item_total": {
                                "currency_code": "USD",
                                "value": price
                            }
                        },
                    }
                }
            ],
            "application_context": {
                "shipping_preference": "NO_SHIPPING"
            }
        })

        response = self.client.execute(create_order)
        data = response.result.__dict__['_dict']

        return data

    def capture_order(self, order_id):
        capture_order = OrdersCaptureRequest(order_id)

        response = self.client.execute(capture_order)
        data = response.result.__dict__['_dict']

        return data
