from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cliente.models import garantir_cliente
from itens_pedido.models import ItemPedido
from pedido.models import Pedido
from produto.models import Produto

LIMITE_POR_ITEM = 20


def _itens_do_carrinho(request):
    """Lê o carrinho da sessão com UMA consulta e descarta produtos que não existem mais."""
    bruto = request.session.get('carrinho', {})
    ids = [int(pk) for pk in bruto if str(pk).isdigit()]
    produtos = Produto.objects.in_bulk(ids)

    itens, total, limpo = [], 0, {}
    for pk in ids:
        produto = produtos.get(pk)
        try:
            quantidade = int(bruto[str(pk)])
        except (TypeError, ValueError):
            continue
        if produto is None or quantidade < 1:
            continue
        quantidade = min(quantidade, LIMITE_POR_ITEM)
        subtotal = produto.valor * quantidade
        total += subtotal
        limpo[str(pk)] = quantidade
        itens.append({'produto': produto, 'quantidade': quantidade, 'item_total': subtotal})

    if limpo != bruto:
        request.session['carrinho'] = limpo
    return itens, total


@require_POST
def addcarrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho = request.session.get('carrinho', {})
    chave = str(produto.id)
    atual = carrinho.get(chave, 0)

    if atual >= LIMITE_POR_ITEM:
        messages.warning(request, f'Limite de {LIMITE_POR_ITEM} unidades de {produto.nome} por pedido.')
    else:
        carrinho[chave] = atual + 1
        request.session['carrinho'] = carrinho
        messages.success(request, f'{produto.nome} adicionado ao carrinho.')

    # Volta para a página de onde o cliente veio (se for do próprio site)
    destino = request.META.get('HTTP_REFERER')
    if destino and url_has_allowed_host_and_scheme(destino, allowed_hosts={request.get_host()},
                                                   require_https=request.is_secure()):
        return redirect(destino)
    return redirect('home')


@require_POST
def removercarrinho(request, produto_id):
    carrinho = request.session.get('carrinho', {})

    if carrinho.pop(str(produto_id), None) is not None:
        request.session['carrinho'] = carrinho
        produto = Produto.objects.filter(id=produto_id).first()
        nome = produto.nome if produto else 'Item'
        messages.success(request, f'{nome} removido do carrinho.')

    return redirect('mostracarrinho')


def mostracarrinho(request):
    carrinho_itens, total = _itens_do_carrinho(request)
    return render(request, 'carrinho.html', {'carrinho_itens': carrinho_itens, 'total': total})


@login_required(login_url='logar')
@require_POST
def finalizar_compra(request):
    itens, total = _itens_do_carrinho(request)
    if not itens:
        return redirect('mostracarrinho')

    cliente = garantir_cliente(request.user)  # contas sem cadastro (ex.: criadas no admin) ganham um mínimo

    with transaction.atomic():  # o pedido é gravado inteiro ou não é gravado
        pedido = Pedido.objects.create(cliente=cliente, data_pedido=timezone.now(), valor_total=total)
        ItemPedido.objects.bulk_create([
            ItemPedido(pedido=pedido, produto=i['produto'], quantidade=i['quantidade'],
                       valor_unitario=i['produto'].valor)
            for i in itens
        ])

    request.session['carrinho'] = {}
    messages.success(request, 'Pedido realizado com sucesso. Obrigado!')
    return redirect('home')
