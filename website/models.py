from django.db import models

class Categoria(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Produto(models.Model):
    nome = models.CharField(max_length=100, unique = True)
    preco = models.DecimalField(max_digits=8, decimal_places=2)
    descricao = models.TextField()
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT)
    em_stock = models.BooleanField(default=True)
    imagem = models.ImageField(upload_to="produtos/")
    favorito = models.BooleanField(default=False)


    def __str__(self):
        return self.nome
    
class ProdutoDestaque(models.Model):
    ORDEM_CHOICES = [
        (1, '1ª posição'),
        (2, '2ª posição'),
        (3, '3ª posição'),
    ]

    produto = models.ForeignKey("Produto", on_delete=models.CASCADE, limit_choices_to={'favorito': True})
    ordem = models.PositiveIntegerField(choices=ORDEM_CHOICES, unique=True)

    class Meta:
        ordering = ['ordem']
        verbose_name = 'Produto em Destaque'
        verbose_name_plural = 'Produtos em Destaque'
        constraints = [
        models.UniqueConstraint(fields=['produto'], name='unique_produto_destaque')
    ]

    def __str__(self):
        return f"{self.ordem}º: {self.produto.nome}"
    
class Parceiro(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    imagem = models.ImageField(upload_to='parceiros/')
    url = models.URLField(blank=True, null=True)
    principal = models.BooleanField(default=False,unique=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields= ['principal'], name='unique_parceiro_principal')
        ]

    def __str__(self):
        if self.principal:
            return f"⭐ {self.nome}"
        return self.nome