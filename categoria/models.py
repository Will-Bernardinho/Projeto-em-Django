from django.db import models


class Categoria(models.Model):
    # único: as páginas do cardápio localizam a categoria pelo nome
    nome = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nome
