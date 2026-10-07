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

## 3. Deploying with GitHub, Vercel, Neon, and Cloudinary

The project is configured for Vercel's Django runtime. Vercel serves collected
static files from its CDN, Neon stores PostgreSQL data, and Cloudinary stores
product photos and future admin uploads. Keep all credentials in Vercel's
Production environment variables; never commit them to Git.

Configure these variables in the Vercel project before deploying:

- `SECRET_KEY`: a long, unique random Django secret
- `DATABASE_URL`: the pooled Neon connection string for `basketbee_vercel`
- `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET`: the existing payment credentials
- `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and
  `CLOUDINARY_API_SECRET`: the Cloudinary account credentials

The existing database and admin account are migrated separately; do not run
`createsuperuser` or seed demo data on the production database.

Before the first production deployment, upload the existing files under
`media/` to Cloudinary, preserving their relative paths. New product images
uploaded through the dashboard will then be stored in Cloudinary automatically.

Vercel detects `manage.py`, uses `basketbee/wsgi.py`, and collects static files
during its build. The `.env` file is for local development only and must not be
committed.

### Demo phone OTP login

The login flow generates a six-digit demo OTP after a valid mobile number is
entered. The code is displayed on the login page; entering it signs in an
existing customer or creates a customer account for that phone number. This is
for demo/testing only and does not send an SMS.

The code expires after five minutes and is limited to five verification
attempts.

## Notes

- Checkout is cash-on-delivery only — no payment gateway is wired up. Adding
  one (Razorpay/Stripe) would slot into the `checkout` view in `store/views.py`.
- The basket is stored in the Django session (not tied to a user account), so
  it's shared across the whole browser session, matching how Blinkit-style
  apps let you shop before signing in.
