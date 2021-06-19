import requests

from paypal.utils.base import PayPalHelper


class PayPalProduct(PayPalHelper):
    def get_products(self):
        res = requests.get(
            self.products_url,
            headers=self.get_request_headers()
        )
        return res.json().get('products', [])

    def get_product(self, product_id):
        # id: PROD-47M73937LE218162X
        res = requests.get(
            f"{self.products_url}/{product_id}",
            headers=self.get_request_headers()
        )
        return res.json()

    def create_product(self, data):
        # If creating a product succeeds, it triggers the CATALOG.PRODUCT.CREATED webhook
        res = requests.post(
            self.products_url,
            headers=self.get_request_headers(),
            json=data
        )
        return res.json()

    def update_product(self, prod_id, paths: dict):
        """
        Can update these fields [description, category, image_url, home_url]
        """
        data: list = list()
        for path, value in paths.items():
            data.append({
                "op": "replace",
                "path": path,
                "value": value
            })
        requests.patch(
            f"{self.products_url}/{prod_id}",
            headers=self.get_request_headers(),
            json=data
        )
