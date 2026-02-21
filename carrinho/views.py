from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from cliente.models import Cliente
from itens_pedido.models import ItemPedido
from pedido.models import Pedido
from produto.models import Produto


def addcarrinho(request, produto_id):
    produto = get_object_or_404(Produto, id=produto_id)
    carrinho = request.session.get('carrinho', {})

    if str(produto_id) in carrinho:
        carrinho[str(produto_id)] += 1

    else:
        carrinho[str(produto_id)] = 1


    request.session['carrinho'] = carrinho
    return redirect('home')

def mostracarrinho(request):
    carrinho= request.session.get('carrinho', {})
    carrinho_itens = []
    total = 0

    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=produto_id)
        item_total = produto.valor * quantidade
        total += item_total

        carrinho_itens.append({
            'produto': produto,
            'quantidade': quantidade,
            'item_total': item_total,
        })

    return render(request, 'carrinho.html', {'carrinho_itens': carrinho_itens, 'total': total})

def finalizar_compra(request):

    carrinho = request.session.get('carrinho', {})

    if not carrinho:
        return redirect('mostracarrinho')  # Redireciona se o carrinho estiver vazio
    else:
        if request.method == 'POST':
           cliente = get_object_or_404(Cliente, usuario=request.user)


    data_atual = timezone.now()
    pedido = Pedido.objects.create(cliente=cliente, data_pedido=data_atual)

    valor_total = 0

    # Itera sobre os itens no carrinho
    for produto_id, quantidade in carrinho.items():
        produto = get_object_or_404(Produto, id=produto_id)
        item_total = produto.valor * quantidade
        valor_total += item_total


        ItemPedido.objects.create(
            pedido=pedido,
            produto=produto,
            quantidade=quantidade,
            valor_unitario=produto.valor
        )


    pedido.valor_total = valor_total
    pedido.save()


    request.session['carrinho'] = {}

    return redirect('home')


# Create your views here.
