from django.contrib import messages
from django.shortcuts import render, redirect

from Principal.decorators import staff_required
from produto.forms import ProdutoForm
from produto.models import Produto


@staff_required
def cadastrar_produto(request):
    form = ProdutoForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        Produto.objects.create(
            nome=d['nome'], descricao=d['descricao'], imagem=d['imagem'],
            valor=d['preco'], quantidade=d['quant'], categoria=d['categoria'],
        )
        messages.success(request, f"{d['nome']} cadastrado no cardápio.")
        return redirect('cadastrar_produto')

    return render(request, 'cadproduto.html', {'form': form})
