from django.db import models
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=16)
    email = models.EmailField()
    cep = models.CharField(max_length=9)
    numero = models.IntegerField()
    compl = models.CharField(max_length=28)

    def __str__(self):
        return self.nome
# Create your models here.

