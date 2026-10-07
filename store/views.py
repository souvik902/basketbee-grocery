from decimal import Decimal
import hashlib
import hmac
import secrets

import requests

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, update_session_auth_hash
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    AddressForm,
    MobileLoginForm,
    OTPVerificationForm,
    ProfileForm,
    RegisterForm,
    ReviewForm,
)

from .models import (
    Address,
    Category,
    Coupon,
    CustomerProfile,
    GroceryPlan,
    GroceryPlanItem,
    Order,
    OrderItem,
    Product,
    Review,
)


# =========================================================
# CONSTANTS
# =========================================================

DELIVERY_FEE = Decimal("20.00")


# =========================================================
# CART FUNCTIONS
# =========================================================

def cart_lines(request):
    cart = request.session.get("cart", {})

    lines = []
    subtotal = Decimal("0")
    saved = Decimal("0")

    for product in Product.objects.filter(
        id__in=cart,
        is_available=True,
    ):
        quantity = min(
            int(cart[str(product.id)]),
            product.stock,
        )

        if quantity:
            lines.append({
                "product": product,
                "quantity": quantity,
                "total": product.selling_price * quantity,
            })

            subtotal += product.selling_price * quantity
            saved += (product.price - product.selling_price) * quantity

    delivery = (
        DELIVERY_FEE
        if subtotal and subtotal < Decimal("500")
        else Decimal("0")
    )

    return lines, subtotal, saved, delivery


# =========================================================
# HOME
# =========================================================

def home(request):
    products = Product.objects.filter(
        is_available=True,
        stock__gt=0,
    )

    return render(request, "home.html", {
        "categories": Category.objects.all(),
        "popular": products[:8],
        "deals": products.exclude(discount_price__isnull=True)[:8],
        "recommended": products.order_by("?")[:4],
        "recent": Product.objects.filter(
            id__in=request.session.get("recent", []),
            is_available=True,
        ),
    })


# =========================================================
# PRODUCTS
# =========================================================

def products(request, category_slug=None):
    queryset = Product.objects.filter(
        is_available=True,
        stock__gt=0,
    ).select_related("category")

    query = request.GET.get("q", "").strip()

    if category_slug:
        queryset = queryset.filter(category__slug=category_slug)

    if query:
        queryset = queryset.filter(
            Q(name__icontains=query)
            | Q(brand__icontains=query)
            | Q(category__name__icontains=query)
        )

    return render(request, "products.html", {
        "products": queryset,
        "query": query,
        "selected_category": category_slug,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_available=True)

    recent = [product.id] + [
        item for item in request.session.get("recent", [])
        if item != product.id
    ]

    request.session["recent"] = recent[:8]

    return render(request, "product_detail.html", {
        "product": product,
        "related": Product.objects.filter(
            category=product.category,
            is_available=True,
        ).exclude(pk=product.pk)[:4],
        "review_form": ReviewForm(),
        "reviews": product.reviews.select_related("user"),
    })


# =========================================================
# CART
# =========================================================

@require_POST
def add_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_available=True)
    cart = request.session.get("cart", {})
    current_quantity = cart.get(str(product.id), 0)

    cart[str(product.id)] = min(current_quantity + 1, product.stock)
    request.session["cart"] = cart

    messages.success(request, f"{product.name} added to your basket.")

    return redirect(request.META.get("HTTP_REFERER", "cart"))


def cart(request):
    lines, subtotal, saved, delivery = cart_lines(request)

    return render(request, "cart.html", {
        "lines": lines,
        "subtotal": subtotal,
        "saved": saved,
        "delivery": delivery,
        "total": subtotal + delivery,
    })


@require_POST
def update_cart(request, product_id, action):
    cart = request.session.get("cart", {})
    key = str(product_id)
    product = get_object_or_404(Product, id=product_id)

    if action == "plus":
        cart[key] = min(cart.get(key, 0) + 1, product.stock)
    elif action == "minus":
        cart[key] = cart.get(key, 1) - 1

    if action == "remove" or cart.get(key, 0) <= 0:
        cart.pop(key, None)

    request.session["cart"] = cart
    return redirect("cart")


# =========================================================
# REGISTER
# =========================================================

def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = RegisterForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        login(request, form.save())
        messages.success(request, "Welcome to BasketBee!")
        return redirect("home")

    return render(request, "register.html", {"form": form})


# =========================================================
# USER LOGIN WITH OTP
# =========================================================

def user_login(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.GET.get("change") == "number":
        for key in (
            "login_phone",
            "login_otp",
            "login_demo_otp",
            "login_otp_sent_at",
            "login_otp_attempts",
            "login_location",
        ):
            request.session.pop(key, None)
        return redirect("login")

    phone_form = MobileLoginForm(request.POST or None)
    otp_form = OTPVerificationForm(
        request.POST
        if request.method == "POST" and request.POST.get("action") == "verify_otp"
        else None
    )
    otp_sent = bool(request.session.get("login_phone"))
    demo_otp = request.session.get("login_demo_otp")

    if (
        request.method == "POST"
        and request.POST.get("action") == "send_otp"
        and phone_form.is_valid()
    ):
        phone = phone_form.cleaned_data["phone"]
        otp = str(secrets.randbelow(900000) + 100000)
        request.session["login_phone"] = phone
        request.session["login_otp"] = make_password(otp)
        request.session["login_demo_otp"] = otp
        request.session["login_otp_sent_at"] = timezone.now().timestamp()
        request.session["login_otp_attempts"] = 0
        request.session["login_location"] = {
            "latitude": request.POST.get("latitude", ""),
            "longitude": request.POST.get("longitude", ""),
        }
        otp_sent = True
        demo_otp = otp
        messages.success(request, "Your demo verification code is ready.")

    elif (
        request.method == "POST"
        and request.POST.get("action") == "verify_otp"
    ):
        phone = request.session.get("login_phone")
        sent_at = request.session.get("login_otp_sent_at", 0)
        attempts = request.session.get("login_otp_attempts", 0)

        if not phone or timezone.now().timestamp() - sent_at > 300:
            request.session.pop("login_phone", None)
            request.session.pop("login_otp_sent_at", None)
            request.session.pop("login_otp", None)
            request.session.pop("login_demo_otp", None)
            request.session.pop("login_otp_attempts", None)
            request.session.pop("login_location", None)
            messages.error(request, "This verification code expired. Request a new one.")
            otp_sent = False

        elif attempts >= 5:
            for key in (
                "login_phone",
                "login_otp",
                "login_demo_otp",
                "login_otp_sent_at",
                "login_otp_attempts",
                "login_location",
            ):
                request.session.pop(key, None)
            messages.error(request, "Too many incorrect attempts. Request a new OTP.")
            otp_sent = False

        elif otp_form.is_valid():
            is_valid_otp = check_password(
                otp_form.cleaned_data["otp"],
                request.session.get("login_otp", ""),
            )

            if is_valid_otp:
                profile = (
                    CustomerProfile.objects
                    .select_related("user")
                    .filter(phone=phone)
                    .first()
                )

                if profile:
                    user = profile.user
                else:
                    user, _ = User.objects.get_or_create(
                        username=f"user_{phone[-10:]}"
                    )
                    CustomerProfile.objects.get_or_create(
                        user=user,
                        defaults={"phone": phone},
                    )

                login(request, user)

                request.session["delivery_location"] = request.session.get(
                    "login_location",
                    {"latitude": "", "longitude": ""},
                )

                for key in (
                    "login_phone",
                    "login_otp_sent_at",
                    "login_otp",
                    "login_demo_otp",
                    "login_otp_attempts",
                    "login_location",
                ):
                    request.session.pop(key, None)

                return redirect(request.GET.get("next", "home"))

            else:
                request.session["login_otp_attempts"] = attempts + 1
                messages.error(request, "That verification code is incorrect.")

        else:
            messages.error(request, "Enter the 6-digit verification code.")

    return render(request, "login.html", {
        "phone_form": phone_form,
        "otp_form": otp_form,
        "otp_sent": otp_sent,
        "demo_otp": demo_otp,
        "login_phone": request.session.get("login_phone", ""),
    })


# =========================================================
# ADMIN LOGIN
# =========================================================

def admin_login(request):
    if request.user.is_staff:
        return redirect("/admin/")

    form = AuthenticationForm(request, data=request.POST or None)

    if request.method == "POST" and form.is_valid():
        user = form.get_user()

        if user.is_staff:
            login(request, user)
            return redirect("/admin/")

        messages.error(request, "This account does not have administrator access.")

    return render(request, "admin_login.html", {"form": form})


# =========================================================
# PROFILE
# =========================================================

@login_required
def profile(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, instance=profile)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")

    return render(request, "profile.html", {
        "form": form,
        "addresses": request.user.addresses.all(),
    })


@login_required
def password_change(request):
    form = PasswordChangeForm(request.user, request.POST or None)

    if request.method == "POST" and form.is_valid():
        update_session_auth_hash(request, form.save())
        messages.success(request, "Password changed.")
        return redirect("profile")

    return render(request, "form_page.html", {
        "form": form,
        "title": "Change password",
    })


@login_required
def address_form(request, pk=None):
    address = (
        get_object_or_404(Address, pk=pk, user=request.user)
        if pk else None
    )

    form = AddressForm(request.POST or None, instance=address)

    if request.method == "POST" and form.is_valid():
        obj = form.save(commit=False)
        obj.user = request.user
        obj.save()
        return redirect("profile")

    return render(request, "form_page.html", {
        "form": form,
        "title": "Edit address" if address else "Add address",
    })


@login_required
@require_POST
def delete_address(request, pk):
    get_object_or_404(Address, pk=pk, user=request.user).delete()
    messages.success(request, "Address removed.")
    return redirect("profile")


# =========================================================
# CHECKOUT + PAYMENT HELPERS
# =========================================================

@login_required
def checkout(request):
    lines, subtotal, saved, delivery = cart_lines(request)

    if not lines:
        messages.info(request, "Your basket is empty.")
        return redirect("cart")

    coupon_discount = Decimal("0")
    code = request.POST.get("coupon", "").strip() if request.method == "POST" else ""

    if code:
        coupon = Coupon.objects.filter(code__iexact=code).first()
        if coupon and coupon.valid_for(subtotal):
            coupon_discount = coupon.discount(subtotal)
            code = coupon.code
        else:
            messages.error(request, "That coupon is invalid or not eligible.")

    total = max(Decimal("0"), subtotal + delivery - coupon_discount)

    # Only COD is created by the normal checkout POST.
    # Online payments always go through the Razorpay endpoints below.
    if request.method == "POST" and request.POST.get("place_order"):
        payment = request.POST.get("payment_method", "cod")

        if payment != "cod":
            return redirect("checkout")

        address = get_object_or_404(
            Address,
            pk=request.POST.get("address"),
            user=request.user,
        )

        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total,
                payment_method="cod",
                payment_status="pending",
            )

            for line in lines:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(pk=line["product"].pk)
                )

                if product.stock < line["quantity"]:
                    raise ValueError(f"{product.name} stock changed. Please try again.")

                product.stock -= line["quantity"]
                product.save(update_fields=["stock"])

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=line["quantity"],
                    price=product.selling_price,
                )

            request.session["cart"] = {}

        messages.success(request, "Your order is placed!")
        return redirect("order_detail", order_number=order.order_number)

    return render(request, "checkout.html", {
        "lines": lines,
        "subtotal": subtotal,
        "saved": saved,
        "delivery": delivery,
        "coupon_discount": coupon_discount,
        "total": total,
        "addresses": request.user.addresses.all(),
        "coupon_code": code,
    })


def _calculate_checkout_total(request, coupon_code=""):
    """Recalculate the payable amount on the server."""
    lines, subtotal, saved, delivery = cart_lines(request)

    if not lines:
        return lines, subtotal, saved, delivery, Decimal("0"), Decimal("0")

    coupon_discount = Decimal("0")
    coupon_code = (coupon_code or "").strip()

    if coupon_code:
        coupon = Coupon.objects.filter(code__iexact=coupon_code).first()
        if coupon and coupon.valid_for(subtotal):
            coupon_discount = coupon.discount(subtotal)

    total = max(Decimal("0"), subtotal + delivery - coupon_discount)
    return lines, subtotal, saved, delivery, coupon_discount, total


# =========================================================
# RAZORPAY - CREATE STANDARD CHECKOUT ORDER
# =========================================================

@login_required
@require_POST
def create_payment(request):
    address_id = request.POST.get("address", "").strip()
    coupon_code = request.POST.get("coupon", "").strip()
    requested_method = request.POST.get("payment_method", "upi").strip().lower()

    if requested_method not in {"upi", "card"}:
        requested_method = "upi"

    if not address_id:
        return JsonResponse({
            "success": False,
            "message": "Please select a delivery address.",
        }, status=400)

    address = get_object_or_404(Address, pk=address_id, user=request.user)
    lines, subtotal, saved, delivery, coupon_discount, total = _calculate_checkout_total(
        request, coupon_code
    )

    if not lines:
        return JsonResponse({
            "success": False,
            "message": "Your basket is empty.",
        }, status=400)

    if total <= 0:
        return JsonResponse({
            "success": False,
            "message": "Order amount must be greater than zero.",
        }, status=400)

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({
            "success": False,
            "message": "Razorpay keys are not configured in settings.py/.env.",
        }, status=500)

    amount_paise = int(total * Decimal("100"))
    receipt = f"basketbee_{request.user.id}_{secrets.token_hex(6)}"

    razorpay_data = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": receipt,
        "notes": {
            "user_id": str(request.user.id),
            "address_id": str(address.id),
            "coupon": coupon_code,
            "requested_method": requested_method,
        },
    }

    try:
        response = requests.post(
            "https://api.razorpay.com/v1/orders",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json=razorpay_data,
            timeout=20,
        )

        if response.status_code not in (200, 201):
            print("RAZORPAY ORDER CREATE ERROR:", response.status_code, response.text)
            return JsonResponse({
                "success": False,
                "message": "Could not create Razorpay payment order.",
            }, status=500)

        razorpay_order = response.json()
        razorpay_order_id = razorpay_order.get("id")

        if not razorpay_order_id:
            return JsonResponse({
                "success": False,
                "message": "Razorpay did not return an order ID.",
            }, status=500)

        # Keep only the temporary payment state in the session.
        # The real Django Order is created after signature verification.
        request.session["pending_razorpay_payment"] = {
            "razorpay_order_id": razorpay_order_id,
            "address_id": address.id,
            "total": str(total),
            "coupon": coupon_code,
            "requested_method": requested_method,
            "amount_paise": amount_paise,
        }
        request.session.modified = True

        # Return both naming styles so old/new frontend code cannot mismatch.
        return JsonResponse({
            "success": True,
            "key": settings.RAZORPAY_KEY_ID,
            "key_id": settings.RAZORPAY_KEY_ID,
            "order_id": razorpay_order_id,
            "razorpay_order_id": razorpay_order_id,
            "amount": amount_paise,
            "currency": "INR",
            "amount_display": f"₹{total:.2f}",
            "payment_method": requested_method,
        })

    except requests.RequestException as error:
        print("RAZORPAY ORDER REQUEST ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Could not connect to Razorpay.",
        }, status=500)
    except Exception as error:
        print("RAZORPAY CREATE PAYMENT ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Could not create online payment.",
        }, status=500)


# =========================================================
# RAZORPAY - VERIFY STANDARD CHECKOUT PAYMENT
# =========================================================

@login_required
@require_POST
def verify_payment(request):
    razorpay_order_id = request.POST.get("razorpay_order_id", "").strip()
    razorpay_payment_id = request.POST.get("razorpay_payment_id", "").strip()
    razorpay_signature = request.POST.get("razorpay_signature", "").strip()

    if not razorpay_order_id or not razorpay_payment_id or not razorpay_signature:
        return JsonResponse({
            "success": False,
            "message": "Payment verification data is incomplete.",
        }, status=400)

    if not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({
            "success": False,
            "message": "Razorpay secret key is not configured.",
        }, status=500)

    pending = request.session.get("pending_razorpay_payment")
    if not pending or pending.get("razorpay_order_id") != razorpay_order_id:
        return JsonResponse({
            "success": False,
            "message": "Payment session expired. Please start payment again.",
        }, status=400)

    generated_signature = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        f"{razorpay_order_id}|{razorpay_payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(generated_signature, razorpay_signature):
        return JsonResponse({
            "success": False,
            "message": "Payment verification failed.",
        }, status=400)

    lines, subtotal, saved, delivery = cart_lines(request)
    if not lines:
        return JsonResponse({
            "success": False,
            "message": "Your basket is empty.",
        }, status=400)

    address = get_object_or_404(
        Address,
        pk=pending.get("address_id"),
        user=request.user,
    )

    total = Decimal(pending.get("total", "0"))
    expected_amount = int(total * Decimal("100"))

    try:
        # Fetch the payment from Razorpay so the server can determine whether
        # it was UPI/card/etc. and confirm the amount/order match.
        payment_response = requests.get(
            f"https://api.razorpay.com/v1/payments/{razorpay_payment_id}",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            timeout=20,
        )

        if payment_response.status_code != 200:
            print("RAZORPAY PAYMENT FETCH ERROR:", payment_response.status_code, payment_response.text)
            return JsonResponse({
                "success": False,
                "message": "Could not verify payment with Razorpay.",
            }, status=500)

        payment_data = payment_response.json()

        if payment_data.get("order_id") != razorpay_order_id:
            return JsonResponse({
                "success": False,
                "message": "Payment order mismatch.",
            }, status=400)

        if int(payment_data.get("amount", 0)) != expected_amount:
            return JsonResponse({
                "success": False,
                "message": "Payment amount mismatch.",
            }, status=400)

        if payment_data.get("status") != "captured":
            return JsonResponse({
                "success": False,
                "message": "Payment has not been captured yet.",
            }, status=400)

        razorpay_method = (payment_data.get("method") or "").lower()
        payment_method = "card" if razorpay_method == "card" else "upi"

        with transaction.atomic():
            # Prevent accidental duplicate order creation if the browser
            # retries the verification request.
            existing = Order.objects.filter(
                user=request.user,
                razorpay_payment_id=razorpay_payment_id,
            ).first()

            if existing:
                request.session.pop("pending_razorpay_payment", None)
                return JsonResponse({
                    "success": True,
                    "paid": True,
                    "message": "Payment already verified.",
                    "order_number": existing.order_number,
                    "redirect_url": reverse(
                        "order_detail",
                        kwargs={"order_number": existing.order_number},
                    ),
                })

            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total,
                payment_method=payment_method,
                payment_status="paid",
            )

            order.razorpay_order_id = razorpay_order_id
            order.razorpay_payment_id = razorpay_payment_id
            order.save(update_fields=[
                "razorpay_order_id",
                "razorpay_payment_id",
            ])

            for line in lines:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(pk=line["product"].pk)
                )

                if product.stock < line["quantity"]:
                    raise ValueError(f"{product.name} stock changed. Please try again.")

                product.stock -= line["quantity"]
                product.save(update_fields=["stock"])

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=line["quantity"],
                    price=product.selling_price,
                )

            request.session["cart"] = {}
            request.session.pop("pending_razorpay_payment", None)
            request.session.modified = True

        return JsonResponse({
            "success": True,
            "paid": True,
            "message": "Payment successful.",
            "order_number": order.order_number,
            "redirect_url": reverse(
                "order_detail",
                kwargs={"order_number": order.order_number},
            ),
        })

    except ValueError as error:
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=400)
    except requests.RequestException as error:
        print("RAZORPAY VERIFY REQUEST ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Could not connect to Razorpay while verifying payment.",
        }, status=500)
    except Exception as error:
        print("VERIFY PAYMENT ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Payment was verified, but the order could not be created.",
        }, status=500)


# =========================================================
# RAZORPAY UPI QR PAYMENT - CREATE QR
# =========================================================

@login_required
@require_POST
def create_qr_payment(request):
    address_id = request.POST.get("address", "").strip()
    coupon_code = request.POST.get("coupon", "").strip()

    if not address_id:
        return JsonResponse({
            "success": False,
            "message": "Please select a delivery address.",
        }, status=400)

    address = get_object_or_404(Address, pk=address_id, user=request.user)
    lines, subtotal, saved, delivery, coupon_discount, total = _calculate_checkout_total(
        request, coupon_code
    )

    if not lines:
        return JsonResponse({
            "success": False,
            "message": "Your basket is empty.",
        }, status=400)

    if total <= 0:
        return JsonResponse({
            "success": False,
            "message": "Order amount must be greater than zero.",
        }, status=400)

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({
            "success": False,
            "message": "Razorpay keys are not configured in settings.py/.env.",
        }, status=500)

    try:
        amount_paise = int(total * Decimal("100"))

        # Create the Django order first, but do NOT reduce stock until QR
        # payment is confirmed.
        with transaction.atomic():
            order = Order.objects.create(
                user=request.user,
                address=address,
                total_amount=total,
                payment_method="upi",
                payment_status="pending",
            )

            for line in lines:
                product = (
                    Product.objects
                    .select_for_update()
                    .get(pk=line["product"].pk)
                )

                if product.stock < line["quantity"]:
                    raise ValueError(f"{product.name} is out of stock.")

                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=line["quantity"],
                    price=product.selling_price,
                )

        qr_data = {
            "type": "upi_qr",
            "name": "BasketBee",
            "usage": "single_use",
            "fixed_amount": True,
            "payment_amount": amount_paise,
            "description": f"BasketBee Order {order.order_number}",
            "notes": {
                "basketbee_order": order.order_number,
                "django_user_id": str(request.user.id),
                "coupon": coupon_code,
            },
        }

        response = requests.post(
            "https://api.razorpay.com/v1/payments/qr_codes",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            json=qr_data,
            timeout=20,
        )

        if response.status_code not in (200, 201):
            try:
                error_response = response.json()
            except requests.exceptions.JSONDecodeError:
                error_response = {}

            error_details = (
                error_response.get("error", {})
                if isinstance(error_response, dict)
                else {}
            )
            if not isinstance(error_details, dict):
                error_details = {}

            error_code = str(error_details.get("code") or "")
            error_message = str(error_details.get("description") or "").strip()
            if not error_message:
                error_message = (
                    "Razorpay rejected the QR request. Check the server log "
                    "for the HTTP status and error code."
                )

            print(
                "RAZORPAY QR CREATE ERROR:",
                response.status_code,
                error_code or "unknown error code",
                error_message,
            )
            order.delete()
            return JsonResponse({
                "success": False,
                "message": error_message,
                "error_code": error_code or None,
            }, status=502)

        qr = response.json()
        qr_id = qr.get("id")
        image_url = qr.get("image_url")

        if not qr_id or not image_url:
            print("RAZORPAY QR RESPONSE MISSING DATA:", qr)
            order.delete()
            return JsonResponse({
                "success": False,
                "message": "Razorpay did not return a valid QR code.",
            }, status=500)

        order.razorpay_qr_id = qr_id
        order.save(update_fields=["razorpay_qr_id"])

        request.session["pending_qr_order_number"] = order.order_number
        request.session.modified = True

        return JsonResponse({
            "success": True,
            "qr_id": qr_id,
            "image_url": image_url,
            "qr_image_url": image_url,
            "amount": amount_paise,
            "amount_display": f"₹{total:.2f}",
            "order_number": order.order_number,
        })

    except ValueError as error:
        print("QR ORDER ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": str(error),
        }, status=400)
    except requests.RequestException as error:
        print("RAZORPAY QR REQUEST ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Could not connect to Razorpay.",
        }, status=500)
    except Exception as error:
        print("QR CREATE ERROR:", error)
        return JsonResponse({
            "success": False,
            "message": "Could not create UPI QR.",
        }, status=500)


# =========================================================
# RAZORPAY UPI QR PAYMENT - CHECK PAYMENT
# =========================================================

@login_required
@require_POST
def check_qr_payment(request):
    qr_id = request.POST.get("qr_id", "").strip()

    if not qr_id:
        return JsonResponse({
            "success": False,
            "status": "failed",
            "message": "QR ID is missing.",
        }, status=400)

    order = get_object_or_404(
        Order,
        razorpay_qr_id=qr_id,
        user=request.user,
    )

    # Already paid: return the same success response without touching stock again.
    if order.payment_status == "paid":
        return JsonResponse({
            "success": True,
            "paid": True,
            "status": "paid",
            "message": "Payment successful.",
            "order_number": order.order_number,
            "redirect_url": reverse(
                "order_detail",
                kwargs={"order_number": order.order_number},
            ),
        })

    if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
        return JsonResponse({
            "success": False,
            "status": "failed",
            "message": "Razorpay keys are not configured.",
        }, status=500)

    try:
        response = requests.get(
            f"https://api.razorpay.com/v1/payments/qr_codes/{qr_id}/payments",
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
            params={"count": 10},
            timeout=20,
        )

        if response.status_code != 200:
            print("RAZORPAY PAYMENT CHECK ERROR:", response.status_code, response.text)
            return JsonResponse({
                "success": False,
                "status": "pending",
                "message": "Could not check payment status right now.",
            }, status=500)

        payment_data = response.json()
        payments = payment_data.get("items", [])
        paid_payment = next(
            (payment for payment in payments if payment.get("status") == "captured"),
            None,
        )

        if not paid_payment:
            return JsonResponse({
                "success": True,
                "paid": False,
                "status": "pending",
                "message": "Payment is still pending.",
            })

        with transaction.atomic():
            order = Order.objects.select_for_update().get(pk=order.pk)

            if order.payment_status != "paid":
                for item in order.items.select_related("product"):
                    product = Product.objects.select_for_update().get(pk=item.product_id)

                    if product.stock < item.quantity:
                        order.payment_status = "failed"
                        order.save(update_fields=["payment_status"])
                        return JsonResponse({
                            "success": False,
                            "status": "failed",
                            "message": f"{product.name} is no longer available in the required quantity.",
                        }, status=409)

                    product.stock -= item.quantity
                    product.save(update_fields=["stock"])

                order.payment_status = "paid"
                order.razorpay_payment_id = paid_payment.get("id")
                order.save(update_fields=[
                    "payment_status",
                    "razorpay_payment_id",
                ])

            request.session["cart"] = {}
            request.session.pop("pending_qr_order_number", None)
            request.session.modified = True

        return JsonResponse({
            "success": True,
            "paid": True,
            "status": "paid",
            "message": "Payment successful.",
            "order_number": order.order_number,
            "redirect_url": reverse(
                "order_detail",
                kwargs={"order_number": order.order_number},
            ),
        })

    except requests.RequestException as error:
        print("RAZORPAY PAYMENT REQUEST ERROR:", error)
        return JsonResponse({
            "success": False,
            "status": "pending",
            "message": "Could not connect to Razorpay.",
        }, status=500)
    except Exception as error:
        print("PAYMENT CHECK ERROR:", error)
        return JsonResponse({
            "success": False,
            "status": "pending",
            "message": "Could not check payment.",
        }, status=500)


# =========================================================
# ORDERS
# =========================================================

@login_required
def orders(request):
    return render(request, "orders.html", {
        "orders": request.user.orders.prefetch_related("items__product"),
    })


@login_required
def order_detail(request, order_number):
    return render(request, "order_detail.html", {
        "order": get_object_or_404(
            Order,
            order_number=order_number,
            user=request.user,
        ),
    })


@login_required
@require_POST
def reorder(request, order_number):
    order = get_object_or_404(
        Order,
        order_number=order_number,
        user=request.user,
    )

    cart = request.session.get("cart", {})

    for item in order.items.select_related("product"):
        product = item.product

        if product.is_available and product.stock:
            cart[str(product.id)] = min(
                cart.get(str(product.id), 0) + item.quantity,
                product.stock,
            )

    request.session["cart"] = cart
    messages.success(request, "Available items were added to your basket.")
    return redirect("cart")


# =========================================================
# GROCERY PLANNER
# =========================================================

@login_required
def planner(request):
    plan, _ = GroceryPlan.objects.get_or_create(user=request.user)

    return render(request, "grocery_plan.html", {
        "plan": plan,
        "products": Product.objects.filter(
            is_available=True,
            stock__gt=0,
        ),
    })


@login_required
@require_POST
def plan_add(request, product_id):
    plan, _ = GroceryPlan.objects.get_or_create(user=request.user)

    GroceryPlanItem.objects.get_or_create(
        plan=plan,
        product_id=product_id,
        day=request.POST.get("day", "Monday"),
    )

    return redirect("planner")


@login_required
@require_POST
def plan_remove(request, pk):
    get_object_or_404(
        GroceryPlanItem,
        pk=pk,
        plan__user=request.user,
    ).delete()

    return redirect("planner")


@login_required
@require_POST
def plan_to_cart(request):
    plan, _ = GroceryPlan.objects.get_or_create(user=request.user)
    cart = request.session.get("cart", {})

    for item in plan.items.select_related("product"):
        product = item.product

        if product.is_available and product.stock:
            cart[str(product.id)] = min(
                cart.get(str(product.id), 0) + item.quantity,
                product.stock,
            )

    request.session["cart"] = cart
    messages.success(request, "Your weekly plan is now in the basket.")
    return redirect("cart")


# =========================================================
# BUDGET
# =========================================================

@login_required
def budget(request):
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        try:
            profile.budget = Decimal(request.POST["budget"])
            profile.save()
            messages.success(request, "Budget saved.")
        except Exception:
            messages.error(request, "Enter a valid budget amount.")

        return redirect("budget")

    _, subtotal, _, delivery = cart_lines(request)
    total = subtotal + delivery

    return render(request, "budget.html", {
        "budget": profile.budget,
        "cart_total": total,
        "remaining": (
            profile.budget - total
            if profile.budget is not None
            else None
        ),
    })


# =========================================================
# PRODUCT REVIEW
# =========================================================

@login_required
@require_POST
def review(request, slug):
    product = get_object_or_404(Product, slug=slug)
    form = ReviewForm(request.POST)

    if form.is_valid():
        Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults=form.cleaned_data,
        )
        messages.success(request, "Thanks for your review!")

    return redirect("product_detail", slug=slug)