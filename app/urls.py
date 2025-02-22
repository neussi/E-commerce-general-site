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
    path('paypal/cancelled/', payment_cancelled, name='payment_cancelled'),
    path('payment/<int:product_id>/', payment_view, name='payment'),
    path('payment/handle/', handle_payment, name='handle_payment'),
    path('payment/success/<int:order_id>/', success_view, name='payment_success'),
    path('payment/invoice/<int:order_id>/', download_invoice, name='download_invoice'),
    path('contact/', contact, name='contact'),
    


]