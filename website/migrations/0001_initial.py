# Generated by Django 5.2 on 2025-05-07 18:26

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ProductCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50, unique=True, verbose_name='Nome')),
            ],
            options={
                'verbose_name': 'Categoria',
                'verbose_name_plural': 'Categorias',
            },
        ),
        migrations.CreateModel(
            name='Partner',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True, verbose_name='Nome')),
                ('image', models.ImageField(upload_to='parceiros/', verbose_name='Imagem')),
                ('url', models.URLField(blank=True, null=True, verbose_name='URL')),
                ('is_main', models.BooleanField(default=False, unique=True, verbose_name='Principal')),
            ],
            options={
                'verbose_name': 'Parceiro',
                'verbose_name_plural': 'Parceiros',
                'constraints': [models.UniqueConstraint(fields=('is_main',), name='unique_main_partner')],
            },
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='Nome')),
                ('slug', models.SlugField(blank=True, unique=True, verbose_name='Slug')),
                ('description', models.TextField(verbose_name='Descrição')),
                ('price', models.DecimalField(decimal_places=2, max_digits=8, verbose_name='Preço')),
                ('stock', models.PositiveIntegerField(verbose_name='Stock')),
                ('favorite', models.BooleanField(default=False, verbose_name='Favorito')),
                ('image', models.ImageField(upload_to='produtos/', verbose_name='Imagem')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Criado em')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Atualizado em')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='website.productcategory', verbose_name='Categoria')),
            ],
            options={
                'verbose_name': 'Produto',
                'verbose_name_plural': 'Produtos',
            },
        ),
        migrations.CreateModel(
            name='FeaturedProduct',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.PositiveIntegerField(choices=[(1, '1ª posição'), (2, '2ª posição'), (3, '3ª posição')], unique=True, verbose_name='Ordem')),
                ('product', models.ForeignKey(limit_choices_to={'favorite': True}, on_delete=django.db.models.deletion.CASCADE, to='website.product', verbose_name='Produto')),
            ],
            options={
                'verbose_name': 'Produto em Destaque',
                'verbose_name_plural': 'Produtos em Destaque',
                'ordering': ['order'],
                'constraints': [models.UniqueConstraint(fields=('product',), name='unique_featured_product')],
            },
        ),
    ]
