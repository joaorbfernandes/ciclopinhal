from django.contrib import admin
from .models import Categoria,Produto,ProdutoDestaque,Parceiro

# Register your models here.

admin.site.register(Produto)
admin.site.register(Categoria)
admin.site.register(ProdutoDestaque)
admin.site.register(Parceiro)