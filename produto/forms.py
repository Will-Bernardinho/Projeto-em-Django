from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError

from categoria.models import Categoria

TAMANHO_MAXIMO_IMAGEM = 5 * 1024 * 1024  # 5 MB
FORMATOS_ACEITOS = {'JPEG', 'PNG', 'WEBP'}


class ProdutoForm(forms.Form):
    categoria = forms.ModelChoiceField(queryset=Categoria.objects.all(), empty_label='Selecione uma categoria')
    nome = forms.CharField(max_length=100)
    descricao = forms.CharField(max_length=1000, label='Descrição')
    quant = forms.IntegerField(min_value=0, max_value=100000, label='Quantidade')
    preco = forms.DecimalField(min_value=Decimal('0.01'), max_value=Decimal('99999999.99'),
                               max_digits=10, decimal_places=2, label='Preço')
    imagem = forms.ImageField()  # confere com o Pillow que o arquivo é mesmo uma imagem

    def clean_imagem(self):
        arquivo = self.cleaned_data['imagem']
        if arquivo.size > TAMANHO_MAXIMO_IMAGEM:
            raise ValidationError('A imagem deve ter no máximo 5 MB.')
        formato = getattr(getattr(arquivo, 'image', None), 'format', None)
        if formato not in FORMATOS_ACEITOS:
            raise ValidationError('Envie uma imagem JPEG, PNG ou WEBP.')
        return arquivo
