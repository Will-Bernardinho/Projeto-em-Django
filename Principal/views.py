from django.conf import settings
from django.db.models import Count, OuterRef, Subquery
from django.shortcuts import render

from Principal.decorators import staff_required
from categoria.models import Categoria
from produto.models import Produto

# (nome no banco, ideograma, nome da rota, numeral) na ordem em que aparecem na home
SECOES = [
    ('Sushi', '寿司', 'sushi', '一'),
    ('Sashimi', '刺身', 'sashimi', '二'),
    ('Temaki', '手巻', 'temaki', '三'),
    ('Sobremesas', '甘味', 'sobremesas', '四'),
    ('Bebidas', '飲物', 'bebidas', '五'),
]


def inicio(request):
    # Uma única consulta traz, de todas as categorias, o total de pratos e a primeira foto
    primeira_foto = (Produto.objects.filter(categoria=OuterRef('pk')).exclude(imagem='')
                     .order_by('id').values('imagem')[:1])
    por_nome = {
        c.nome: c
        for c in Categoria.objects.filter(nome__in=[s[0] for s in SECOES])
                          .annotate(total=Count('produto'), foto=Subquery(primeira_foto))
    }

    categorias = []
    for nome, jp, rota, numeral in SECOES:
        c = por_nome.get(nome)
        categorias.append({
            'nome': nome, 'jp': jp, 'rota': rota, 'numeral': numeral,
            'total': c.total if c else 0,
            'imagem': c.foto if c and c.foto else None,  # caminho relativo ao MEDIA_ROOT
        })

    novidades = Produto.objects.exclude(imagem='').select_related('categoria').order_by('-id')[:4]
    return render(request, 'inicio.html', {'categorias': categorias, 'novidades': novidades})


def historia(request):
    return render(request, 'historia.html')


@staff_required
def administrativo(request):
    return render(request, 'menuadm.html')


def _menu_categoria(request, nome, template):
    produtos = Produto.objects.filter(categoria__nome=nome)
    return render(request, template, {'produtos': produtos})


def sushi(request):
    return _menu_categoria(request, 'Sushi', 'sushi.html')


def sashimi(request):
    return _menu_categoria(request, 'Sashimi', 'Sashimi.html')


def temaki(request):
    return _menu_categoria(request, 'Temaki', 'Temaki.html')


def sobremesas(request):
    return _menu_categoria(request, 'Sobremesas', 'Sobremesas.html')


def bebidas(request):
    return _menu_categoria(request, 'Bebidas', 'Bebidas.html')


def contato(request):
    return render(request, 'contatos.html')
