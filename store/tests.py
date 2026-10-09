from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import Address, Category, Coupon, CustomerProfile, Product


class HomeCarouselTests(TestCase):
	def test_home_carousel_has_distinct_grocery_images(self):
		response = self.client.get(reverse("home"))

		self.assertEqual(response.status_code, 200)
		slides = response.context["promo_slides"]
		images = [slide["image"] for slide in slides]

		self.assertEqual(len(slides), 5)
		self.assertEqual(len(images), len(set(images)))
		self.assertEqual(set(images), {
			"products/Apples-184940975-770x533-1_jpg.webp",
			"products/Brown-eggs.webp",
			"products/500-regular-ctc-assam-tea-with-elaichi-long-cinnamon-1-box-original-imahhmxaepbuvt9y.webp",
			"products/7840058004055.webp",
			"products/images5.jpg",
		})
		self.assertContains(response, 'data-slide-total>05</span>')


class PhoneLoginTests(TestCase):
	def test_login_uses_basketbee_phone_flow(self):
		response = self.client.get(reverse("login"))

		self.assertContains(response, 'alt="BasketBee"')
		self.assertContains(response, "Log in or Sign up")
		self.assertContains(response, 'name="phone"')

	@override_settings(DEBUG=True)
	def test_valid_otp_signs_in_and_keeps_requested_location(self):
		login_url = reverse("login")
		phone = "9876543210"
		location = {"latitude": "22.5726", "longitude": "88.3639"}

		response = self.client.post(login_url, {
			"action": "send_otp",
			"phone": phone,
			**location,
		})
		self.assertEqual(response.status_code, 200)
		otp = response.context["demo_otp"]
		self.assertRegex(otp, r"^\d{6}$")
		self.assertContains(response, f"<strong>{otp}</strong>")

		response = self.client.post(login_url, {
			"action": "verify_otp",
			"otp": otp,
		})
		user = User.objects.get(username=f"user_{phone[-10:]}")
		self.assertRedirects(response, reverse("home"))
		self.assertEqual(int(self.client.session["_auth_user_id"]), user.pk)
		self.assertEqual(CustomerProfile.objects.get(user=user).phone, phone)
		self.assertEqual(self.client.session["delivery_location"], location)

	@override_settings(DEBUG=True)
	def test_invalid_otp_shows_feedback_in_modal(self):
		login_url = reverse("login")
		self.client.post(login_url, {"action": "send_otp", "phone": "9876543210"})

		response = self.client.post(login_url, {
			"action": "verify_otp",
			"otp": "000000",
		})

		self.assertContains(response, "That verification code is incorrect.")
		self.assertContains(response, 'class="auth-feedback"')

class CouponCheckoutTests(TestCase):
	def test_checkout_does_not_show_admin_login_to_customer(self):
		user = User.objects.create_user(username="checkout-buyer")
		category = Category.objects.create(name="Checkout navigation test")
		product = Product.objects.create(
			name="Checkout groceries",
			category=category,
			description="",
			price=Decimal("200.00"),
			brand="BasketBee",
			unit="pack",
			stock=3,
		)
		self.client.force_login(user)
		session = self.client.session
		session["cart"] = {str(product.pk): 1}
		session.save()

		response = self.client.get(reverse("checkout"))

		self.assertEqual(response.status_code, 200)
		self.assertNotContains(response, "Admin login")

	def test_checkout_applies_lowercase_admin_coupon(self):
		user = User.objects.create_user(username="coupon-buyer", password="test-pass")
		category = Category.objects.create(name="Coupon test")
		product = Product.objects.create(
			name="Test groceries",
			category=category,
			description="",
			price=Decimal("200.00"),
			brand="BasketBee",
			unit="pack",
			stock=3,
		)
		Coupon.objects.create(
			code="fdjfdgvkf",
			percent=10,
			minimum_amount=Decimal("50.00"),
			expires_at=timezone.now() + timedelta(days=1),
		)
		self.client.force_login(user)
		session = self.client.session
		session["cart"] = {str(product.pk): 1}
		session.save()

		for entered_code in ("FDJFDGVKF", "fdjfdgvkf"):
			with self.subTest(entered_code=entered_code):
				response = self.client.post(reverse("checkout"), {"coupon": entered_code})

				self.assertEqual(response.status_code, 200)
				self.assertEqual(response.context["coupon_discount"], Decimal("20.00"))
				self.assertEqual(response.context["coupon_code"], "fdjfdgvkf")


class CreateQrPaymentTests(TestCase):
	@override_settings(RAZORPAY_KEY_ID="rzp_test_key", RAZORPAY_KEY_SECRET="test_secret")
	def test_qr_api_error_is_returned_without_creating_an_order(self):
		user = User.objects.create_user(username="qr-buyer")
		address = Address.objects.create(
			user=user,
			full_name="QR Buyer",
			phone="9876543210",
			house="1",
			street="Main Road",
			area="Market",
			city="Kolkata",
			state="West Bengal",
			pin_code="700001",
		)
		category = Category.objects.create(name="QR test")
		product = Product.objects.create(
			name="QR groceries",
			category=category,
			description="",
			price=Decimal("200.00"),
			brand="BasketBee",
			unit="pack",
			stock=3,
		)
		self.client.force_login(user)
		session = self.client.session
		session["cart"] = {str(product.pk): 1}
		session.save()

		response_body = {
			"error": {
				"code": "BAD_REQUEST_ERROR",
				"description": "QR Codes are not enabled for this account.",
			},
		}
		with patch("store.views.requests.post") as razorpay_post:
			razorpay_post.return_value.status_code = 400
			razorpay_post.return_value.json.return_value = response_body

			response = self.client.post(
				reverse("create_qr_payment"),
				{"address": address.pk},
			)

		self.assertEqual(response.status_code, 502)
		self.assertEqual(response.json()["error_code"], "BAD_REQUEST_ERROR")
		self.assertEqual(
			response.json()["message"],
			"QR Codes are not enabled for this account.",
		)
		self.assertFalse(user.orders.exists())
