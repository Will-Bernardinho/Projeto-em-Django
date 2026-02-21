from django.db import models

from cliente.models import Cliente


# Create your models here.

class Pedido(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    data_pedido = models.DateTimeField()
    valor_total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f'Pedido {self.id} - {self.cliente}'
from django.db import models

# Create your models here.
