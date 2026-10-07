from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models

from categoria.models import Categoria


class Produto(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    imagem = models.ImageField(upload_to='produtos/')
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0,
                                validators=[MinValueValidator(Decimal('0'))])
    quantidade = models.PositiveIntegerField(default=0)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)

    def __str__(self):
        return self.nome
