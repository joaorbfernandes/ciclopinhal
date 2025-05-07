from django.urls import path
from .views import homepage, ProductListView, ProductDetailView

urlpatterns = [
    path('', homepage, name='homepage'), 
    path('products/', ProductListView.as_view(), name='product_list'), 
    path('product/<slug:slug>/', ProductDetailView.as_view(), name='product_detail'), 
]
