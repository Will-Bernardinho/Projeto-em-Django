from django.db import models

from pedido.models import Pedido
from produto.models import Produto


# Create your models here.

class ItemPedido(models.Model):
    pedido = models.ForeignKey(Pedido, related_name='itens', on_delete=models.CASCADE)
    produto = models.ForeignKey(Produto, on_delete=models.CASCADE)
    quantidade = models.PositiveIntegerField(default=1)  # Quantidade do produto no pedido
    valor_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.quantidade} x {self.produto.nome}'


from django.db import models

# Create your models here.
