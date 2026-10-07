from django.contrib.auth.models import User
from django.db import models


class Cliente(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=16)
    email = models.EmailField()
    cep = models.CharField(max_length=9)
    numero = models.IntegerField()
    compl = models.CharField(max_length=28)

    def __str__(self):
        return self.nome


def garantir_cliente(usuario, **dados):
    """Devolve o cadastro de cliente do usuário, criando um mínimo (sem endereço) se ainda não existir.

    O projeto é para testes e apresentações: basta ter usuário e senha para comprar. Os demais
    campos ficam vazios (texto '') ou zero, sem exigir mudança na estrutura do banco. Valores
    informados em `dados` (quando preenchidos) substituem esses padrões na criação.
    """
    padrao = {
        'nome': usuario.get_username(),
        'telefone': '',
        'email': usuario.email or '',
        'cep': '',
        'numero': 0,
        'compl': '',
    }
    padrao.update({campo: valor for campo, valor in dados.items() if valor not in (None, '')})
    cliente, _ = Cliente.objects.get_or_create(usuario=usuario, defaults=padrao)
    return cliente
