from django.core.management.base import BaseCommand

from store.models import Category, Product

CATEGORIES = [
    ("Vegetables", "🥦"),
    ("Fruits", "🍎"),
    ("Dairy & bread", "🥛"),
    ("Atta, rice & dal", "🌾"),
    ("Snacks", "🍪"),
    ("Beverages", "🧃"),
    ("Household", "🧴"),
]

PRODUCTS = [
    ("Onion", "Vegetables", 32, 38, "1", "kg", 40, 8),
    ("Tomato", "Vegetables", 28, None, "1", "kg", 35, 8),
    ("Potato", "Vegetables", 24, 28, "1", "kg", 50, 8),
    ("Banana", "Fruits", 45, None, "1", "dozen", 20, 10),
    ("Apple (Shimla)", "Fruits", 149, 179, "1", "kg", 15, 12),
    ("Amul Toned Milk", "Dairy & bread", 29, None, "500", "ml", 60, 9),
    ("Brown Bread", "Dairy & bread", 45, 50, "400", "g", 25, 9),
    ("Paneer", "Dairy & bread", 89, 99, "200", "g", 18, 10),
    ("Tata Atta", "Atta, rice & dal", 259, 279, "5", "kg", 30, 12),
    ("Basmati Rice", "Atta, rice & dal", 149, 169, "1", "kg", 22, 12),
    ("Toor Dal", "Atta, rice & dal", 139, None, "1", "kg", 26, 12),
    ("Lays Classic", "Snacks", 20, None, "52", "g", 80, 9),
    ("Parle-G Biscuit", "Snacks", 10, None, "70", "g", 100, 9),
    ("Real Mixed Fruit Juice", "Beverages", 110, 120, "1", "l", 24, 11),
    ("Tata Tea Gold", "Beverages", 135, 150, "250", "g", 28, 11),
    ("Surf Excel", "Household", 199, 220, "1", "kg", 20, 15),
    ("Vim Dishwash Gel", "Household", 89, 99, "500", "ml", 30, 15),
]


class Command(BaseCommand):
    help = "Seed BasketBee with a starter set of categories and products."

    def handle(self, *args, **options):
        cat_objs = {}
        for i, (name, icon) in enumerate(CATEGORIES):
            cat, _ = Category.objects.get_or_create(
                name=name, defaults={"icon": icon, "order": i}
            )
            cat_objs[name] = cat

        created = 0
        for name, cat_name, price, mrp, unit_value, unit, stock, mins in PRODUCTS:
            _, was_created = Product.objects.get_or_create(
                name=name,
                defaults=dict(
                    category=cat_objs[cat_name],
                    price=price,
                    mrp=mrp,
                    unit_value=unit_value,
                    unit=unit,
                    stock=stock,
                    delivery_minutes=mins,
                ),
            )
            created += 1 if was_created else 0

        self.stdout.write(self.style.SUCCESS(
            f"Seeded {len(cat_objs)} categories and {created} new products."
        ))
