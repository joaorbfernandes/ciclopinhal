from django.urls import path
from . import views

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('produtos/', views.lista_produtos, name='lista_produtos'),
    path('produto/<int:pk>/', views.detalhe_produto, name='detalhe_produto'),
    # outras rotas futuras...
]
