from django.contrib import admin
from .models import Product, ProductCategory, FeaturedProduct, Partner
from django.utils.html import format_html


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'category', 'image_tag')
    list_filter = ('category',)
    search_fields = ('name', 'description')
    
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="60" style="object-fit: cover;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Imagem'


@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


@admin.register(FeaturedProduct)
class FeaturedProductAdmin(admin.ModelAdmin):
    list_display = ('product',)


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ('name', 'image_tag')
    
    def image_tag(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" style="object-fit: contain;" />', obj.image.url)
        return "-"
    image_tag.short_description = 'Logo'