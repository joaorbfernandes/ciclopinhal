from django.shortcuts import render, get_object_or_404
from .models import Produto, ProdutoDestaque, Parceiro

# Create your views here.

def homepage(request):
    destaques = ProdutoDestaque.objects.select_related('produto').order_by('ordem')[:6]
    parceiros = Parceiro.objects.order_by('-principal', 'nome')[:6]
    return render(request, 'website/home/homepage.html', {
        'destaques': destaques,
        'parceiros': parceiros,
        })

def lista_produtos(request):
    produtos= Produto.objects.all()
    return render(request, 'website/produtos/lista_produtos.html', {'produtos': produtos})

def detalhe_produto(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    return render(request, 'website/produtos/detalhe_produto.html', {"produto": produto})

