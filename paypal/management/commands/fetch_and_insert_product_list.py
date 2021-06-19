from django.core.management.base import BaseCommand

from paypal.models import Product
from paypal.utils.product import PayPalProduct


class Command(BaseCommand):
    help = 'Fetches and Inserts PayPal product list'

    def _print_exception(self, e: Exception, prefix: str = None):
        prefix = f'{prefix} | ' if prefix else ''
        self.stdout.write(self.style.ERROR(f"{prefix}{type(e).__name__} | {e}"))

    def handle(self, *args, **options):
        paypal_helper = PayPalProduct()
        paypal_products = paypal_helper.get_products()
        products = []
        product_ids = []

        for product in paypal_products:
            if not Product.objects.filter(product_id=product.get('id')).exists():
                product_ids.append(product.get('id'))

        for product_id in product_ids:
            product = paypal_helper.get_product(product_id)
            products.append(Product(
                product_id=product.get('id'),
                name=product.get('name'),
                description=product.get('description'),
                type=product.get('type'),
                category=product.get('category'),
                image_url=product.get('image_url', ''),
                home_url=product.get('home_url', ''),
                create_time=product.get('create_time'),
                update_time=product.get('update_time'),
                links=product.get('links')
            ))

        Product.objects.bulk_create(products, batch_size=20)

        self.stdout.write(
            self.style.SUCCESS(
                f"Fetched {len(paypal_products)} products and inserted {len(product_ids)} products successfully"
            )
        )
