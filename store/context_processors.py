def site_data(request):
    cart=request.session.get('cart', {})
    return {'nav_categories': __import__('store.models',fromlist=['Category']).Category.objects.all()[:8], 'cart_count':sum(cart.values())}
