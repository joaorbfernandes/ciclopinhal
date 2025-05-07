from django.contrib import admin
from .models import Product, ProductCategory, FeaturedProduct, Partner


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'stock', 'favorite', 'category')
    list_filter = ('favorite', 'category')
    search_fields = ('name', 'description')
    prepopulated_fields = {"slug": ("name",)}
    ordering = ['-created_at']


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'order')
    ordering = ('order',)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_main')
    list_filter = ('is_main',)
    search_fields = ('name',)