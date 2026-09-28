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

## 3. Deploying with GitHub and Vercel

The repository includes a Vercel WSGI entrypoint, WhiteNoise static-file
handling, and a production PostgreSQL configuration. SQLite is intentionally
used only for local development because Vercel's filesystem is ephemeral.

1. Create a GitHub repository, then push this project:
   ```bash
   git add .
   git commit -m "Prepare BasketBee for Vercel"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
   git push -u origin main
   ```
2. In Vercel, choose **Add New Project**, import the GitHub repository, and
   deploy with the detected Python settings.
3. Add these Vercel environment variables for **Production**, **Preview**, and
   **Development** as appropriate:
   - `SECRET_KEY`: a long random value
   - `DATABASE_URL`: a hosted PostgreSQL connection string from Neon, Supabase,
     or another PostgreSQL provider
   - `ALLOWED_HOSTS`: your custom domain, if you use one
   - `CSRF_TRUSTED_ORIGINS`: your HTTPS custom domain, if you use one
4. Redeploy. Vercel runs `python manage.py collectstatic --noinput` during the
   build, and `basketbee/wsgi.py` serves the Django application.
5. Run migrations against the hosted database from a local shell using the
   same `DATABASE_URL`, then create the owner account:
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

Product images uploaded through the dashboard need object storage in production
because files written to Vercel are not persistent. Use S3-compatible storage
before relying on uploaded images in the live store.

## Notes

- Checkout is cash-on-delivery only — no payment gateway is wired up. Adding
  one (Razorpay/Stripe) would slot into the `checkout` view in `store/views.py`.
- The basket is stored in the Django session (not tied to a user account), so
  it's shared across the whole browser session, matching how Blinkit-style
  apps let you shop before signing in.
