# BasketBee 🐝

A quick-commerce grocery storefront (Blinkit-style) built with **HTML/CSS** on the
front end and **Python + Django** on the back end. Shoppers browse categories,
add items to a basket, and check out with cash-on-delivery. Shop owners get a
login-protected dashboard to **add, edit, and remove products at any time —
even after the site has been deployed**, with no code changes or redeploys needed.

## Features

- Home page with search, scrollable category chips, and a product grid
- Product detail pages, session-based basket, AJAX add-to-cart (no page reloads)
- Checkout flow that creates an `Order` + `OrderItem`s in the database
- **Admin dashboard** (`/owner/dashboard/`):
  - Add new products (name, category, price, MRP, unit, stock, image, delivery time)
  - Edit or delete any existing product
  - Add new categories
  - See live stats (products, low stock, orders) and recent orders
- Django admin (`/admin/`) also available for power-user management
- Custom "honeycomb" visual identity — no generic template look

## Project layout

```
basketbee/
├── manage.py
├── requirements.txt
├── basketbee/            # project settings, urls
└── store/                # the app: models, views, forms, templates, static
    ├── models.py         # Category, Product, Order, OrderItem
    ├── cart.py            # session-based basket helper
    ├── views.py           # storefront + owner dashboard views
    ├── forms.py
    ├── urls.py
    ├── admin.py
    ├── management/commands/seed_demo.py   # demo data seeder
    ├── templates/store/  # HTML templates
    └── static/store/     # css/js
```

## 1. Local setup

```bash
# from inside the basketbee/ folder
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt

python manage.py migrate
python manage.py seed_demo      # optional: loads demo categories & products

# create your shop-owner login
python manage.py createsuperuser

python manage.py runserver
```

Visit:
- **Storefront:** http://127.0.0.1:8000/
- **Admin login:** http://127.0.0.1:8000/owner/login/
- **Django admin:** http://127.0.0.1:8000/admin/

Log in with the superuser account you created — any account with `is_staff=True`
can access the owner dashboard.

## 2. Adding products after deployment

This is the core requirement: the shop owner doesn't touch code after the site
is live. Once deployed, they:

1. Go to `yourdomain.com/owner/login/` and sign in.
2. Click **"+ Add new product"** on the admin dashboard.
3. Fill in the name, category, price, unit (kg/g/l/ml/piece/pack/dozen), stock,
   an optional photo, and how many minutes it takes to deliver.
4. Save — the product appears on the storefront immediately.

They can also add new categories, edit prices/stock, or remove a product, all
from the same dashboard, at any time, from any device.

## 3. Deploying

The app is a standard Django project, so it deploys to any Django-friendly host
(Render, Railway, PythonAnywhere, a VPS, etc.). Rough steps for a typical host:

1. **Environment variables** — don't ship the dev `SECRET_KEY` or `DEBUG=True`.
   In `basketbee/settings.py`, switch to reading from the environment, e.g.:
   ```python
   import os
   SECRET_KEY = os.environ["SECRET_KEY"]
   DEBUG = os.environ.get("DEBUG", "False") == "True"
   ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
   ```
2. **Static files** — `whitenoise` is already in `requirements.txt`. Add it to
   `MIDDLEWARE` (just below `SecurityMiddleware`) and run:
   ```bash
   python manage.py collectstatic
   ```
3. **Database** — SQLite works for a demo; for real traffic, switch
   `DATABASES` to Postgres (most hosts provide a `DATABASE_URL`; the
   `dj-database-url` package makes this a one-liner).
4. **Media uploads** (product photos) — on most PaaS hosts the filesystem
   isn't persistent, so point `MEDIA_ROOT`/`MEDIA_URL` at S3 or another
   object store for production (e.g. via `django-storages`). Fine to leave
   as local disk for a quick demo.
5. **Run with a real server**, not `runserver`:
   ```bash
   gunicorn basketbee.wsgi:application
   ```
6. Create your production shop-owner account with
   `python manage.py createsuperuser` once, after the first deploy.

## Notes

- Checkout is cash-on-delivery only — no payment gateway is wired up. Adding
  one (Razorpay/Stripe) would slot into the `checkout` view in `store/views.py`.
- The basket is stored in the Django session (not tied to a user account), so
  it's shared across the whole browser session, matching how Blinkit-style
  apps let you shop before signing in.
