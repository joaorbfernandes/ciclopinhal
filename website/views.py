from django.shortcuts import render
from django.views.generic import ListView, DetailView
from .models import Product, FeaturedProduct, Partner


# Homepage with featured products and partners
def homepage(request):
    highlights = FeaturedProduct.objects.select_related('product').order_by('order')[:6]
    partners = Partner.objects.order_by('-is_main', 'name')[:6]
    return render(request, 'website/home/homepage.html', {
        'highlights': highlights,
        'partners': partners,
    })


# Product list (CBV)
class ProductListView(ListView):
    model = Product
    template_name = 'website/products/product_list.html'
    context_object_name = 'products'
    queryset = Product.objects.all()


# Product detail (CBV)
class ProductDetailView(DetailView):
    model = Product
    template_name = 'website/products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'

