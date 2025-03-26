from django.urls import path
from .views import *

urlpatterns = [
    path('', home, name='home'), 
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register, name='register'),
    path('catalogue/', catalogue, name='catalogue'), 
    path('profile/<int:user_id>/', user_profile, name='profile'),
    path('add_product/', add_product, name='add_product'),
    path('product/update/<int:product_id>/', update_product, name='update_product'),
    path('product/delete/<int:product_id>/', delete_product, name='delete_product'),
    path('product/<int:product_id>/', product_detail, name='product_detail'),
    path('contact/', contact, name='contact'),

    path('cart/', cart_view, name='cart'),
    path('add-to-cart/<int:product_id>/', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', remove_from_cart, name='remove_from_cart'),
    path('update-cart-item/<int:item_id>/', update_cart_item, name='update_cart_item'),
    path('checkout/', checkout, name='checkout'),


    path('checkout/', checkout, name='checkout'),
    path('handle-payment/', handle_cart_payment, name='handle_payment'),
    path('payment/success/', payment_success, name='payment_success'),
    path('payment/cancelled/', payment_cancelled, name='payment_cancelled'),
    path('download-invoice/<int:order_id>/', download_invoice, name='download_invoice'),


]