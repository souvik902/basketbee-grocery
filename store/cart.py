from decimal import Decimal

from .models import Product

CART_SESSION_KEY = "basketbee_cart"


class Cart:
    """A tiny session-backed cart: {product_id: quantity}."""

    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(CART_SESSION_KEY)
        if cart is None:
            cart = self.session[CART_SESSION_KEY] = {}
        self.cart = cart

    def add(self, product, quantity=1):
        pid = str(product.id)
        self.cart[pid] = self.cart.get(pid, 0) + quantity
        if self.cart[pid] <= 0:
            del self.cart[pid]
        self.save()

    def set_quantity(self, product, quantity):
        pid = str(product.id)
        if quantity <= 0:
            self.cart.pop(pid, None)
        else:
            self.cart[pid] = quantity
        self.save()

    def remove(self, product):
        pid = str(product.id)
        if pid in self.cart:
            del self.cart[pid]
            self.save()

    def save(self):
        self.session.modified = True

    def clear(self):
        self.session[CART_SESSION_KEY] = {}
        self.save()

    def __len__(self):
        return sum(self.cart.values())

    def __iter__(self):
        ids = self.cart.keys()
        products = Product.objects.filter(id__in=ids)
        for product in products:
            qty = self.cart[str(product.id)]
            yield {
                "product": product,
                "quantity": qty,
                "subtotal": product.price * qty,
            }

    def get_total(self):
        return sum(item["subtotal"] for item in self)
