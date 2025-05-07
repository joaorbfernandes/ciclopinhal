from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.utils.translation import gettext_lazy as _ 

# Model for product categories
class ProductCategory(models.Model):
    name = models.CharField(_("Nome"), max_length=50, unique=True)

    class Meta:
        verbose_name = _("Categoria")
        verbose_name_plural = _("Categorias")

    def __str__(self):
        return self.name


# Model for main product listing
class Product(models.Model):
    name = models.CharField(_("Nome"), max_length=100)
    slug = models.SlugField(_("Slug"), unique=True, blank=True)
    description = models.TextField(_("Descrição"))
    price = models.DecimalField(_("Preço"), max_digits=8, decimal_places=2)
    stock = models.PositiveIntegerField(_("Stock"))
    favorite = models.BooleanField(_("Favorito"), default=False)
    image = models.ImageField(_("Imagem"), upload_to="produtos/")
    category = models.ForeignKey(
        ProductCategory,
        verbose_name=_("Categoria"),
        on_delete=models.PROTECT
    )
    created_at = models.DateTimeField(_("Criado em"), auto_now_add=True)
    updated_at = models.DateTimeField(_("Atualizado em"), auto_now=True)

    class Meta:
        verbose_name = _("Produto")
        verbose_name_plural = _("Produtos")

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("product_detail", kwargs={"slug": self.slug})

    def __str__(self):
        return self.name


# Model for homepage featured products
class FeaturedProduct(models.Model):
    ORDER_CHOICES = [
        (1, _("1ª posição")),
        (2, _("2ª posição")),
        (3, _("3ª posição")),
    ]

    product = models.ForeignKey(
        Product,
        verbose_name=_("Produto"),
        on_delete=models.CASCADE,
        limit_choices_to={'favorite': True}
    )
    order = models.PositiveIntegerField(_("Ordem"), choices=ORDER_CHOICES, unique=True)

    class Meta:
        ordering = ['order']
        verbose_name = _("Produto em Destaque")
        verbose_name_plural = _("Produtos em Destaque")
        constraints = [
            models.UniqueConstraint(fields=['product'], name='unique_featured_product')
        ]

    def __str__(self):
        return f"{self.order}º: {self.product.name}"


# Model for partner logos/links
class Partner(models.Model):
    name = models.CharField(_("Nome"), max_length=100, unique=True)
    image = models.ImageField(_("Imagem"), upload_to='parceiros/')
    url = models.URLField(_("URL"), blank=True, null=True)
    is_main = models.BooleanField(_("Principal"), default=False, unique=True)

    class Meta:
        verbose_name = _("Parceiro")
        verbose_name_plural = _("Parceiros")
        constraints = [
            models.UniqueConstraint(fields=['is_main'], name='unique_main_partner')
        ]

    def __str__(self):
        return f"⭐ {self.name}" if self.is_main else self.name
