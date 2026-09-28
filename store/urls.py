from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views


urlpatterns = [

    # =========================================================
    # HOME
    # =========================================================

    path(
        '',
        views.home,
        name='home'
    ),


    # =========================================================
    # PRODUCTS
    # =========================================================

    path(
        'products/',
        views.products,
        name='products'
    ),

    path(
        'category/<slug:category_slug>/',
        views.products,
        name='category'
    ),

    path(
        'product/<slug:slug>/',
        views.product_detail,
        name='product_detail'
    ),

    path(
        'product/<int:product_id>/add/',
        views.add_cart,
        name='add_cart'
    ),

    path(
        'product/<slug:slug>/review/',
        views.review,
        name='review'
    ),


    # =========================================================
    # CART
    # =========================================================

    path(
        'cart/',
        views.cart,
        name='cart'
    ),

    path(
        'cart/<int:product_id>/<str:action>/',
        views.update_cart,
        name='update_cart'
    ),


    # =========================================================
    # AUTHENTICATION
    # =========================================================

    path(
        'register/',
        views.register,
        name='register'
    ),

    path(
        'login/',
        views.user_login,
        name='login'
    ),

    path(
        'admin-login/',
        views.admin_login,
        name='admin_login'
    ),

    path(
        'logout/',
        LogoutView.as_view(),
        name='logout'
    ),


    # =========================================================
    # PROFILE
    # =========================================================

    path(
        'profile/',
        views.profile,
        name='profile'
    ),

    path(
        'password/',
        views.password_change,
        name='password_change'
    ),


    # =========================================================
    # ADDRESS
    # =========================================================

    path(
        'address/add/',
        views.address_form,
        name='address_add'
    ),

    path(
        'address/<int:pk>/edit/',
        views.address_form,
        name='address_edit'
    ),

    path(
        'address/<int:pk>/delete/',
        views.delete_address,
        name='address_delete'
    ),


    # =========================================================
    # CHECKOUT
    # =========================================================

    path(
        'checkout/',
        views.checkout,
        name='checkout'
    ),


    # =========================================================
    # RAZORPAY ONLINE PAYMENT
    # =========================================================

    # Create Razorpay payment order
    path(
        'payment/create/',
        views.create_payment,
        name='create_payment'
    ),

    # Verify successful Razorpay payment
    path(
        'payment/verify/',
        views.verify_payment,
        name='verify_payment'
    ),


    # =========================================================
    # RAZORPAY UPI QR PAYMENT
    # =========================================================

    # Create dynamic Razorpay UPI QR
    path(
        'payment/qr/create/',
        views.create_qr_payment,
        name='create_qr_payment'
    ),

    # Check whether QR payment is completed
    path(
        'payment/qr/check/',
        views.check_qr_payment,
        name='check_qr_payment'
    ),


    # =========================================================
    # ORDERS
    # =========================================================

    path(
        'orders/',
        views.orders,
        name='orders'
    ),

    path(
        'orders/<str:order_number>/',
        views.order_detail,
        name='order_detail'
    ),

    path(
        'orders/<str:order_number>/reorder/',
        views.reorder,
        name='reorder'
    ),

]