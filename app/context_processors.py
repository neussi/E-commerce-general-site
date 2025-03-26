from .models import Cart

def cart_items_count(request):
    """Context processor to get cart items count."""
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user, ordered=False)
            return {'cart_items_count': cart.items.count()}
        except Cart.DoesNotExist:
            return {'cart_items_count': 0}
    return {'cart_items_count': 0}