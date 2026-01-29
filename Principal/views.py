from django.shortcuts import render

from categoria.models import Categoria
from produto.models import Produto


# Create your views here.
def inicio(request):
    return render(request, template_name='home.html')

def historia (request):
    return render(request, 'historia.html')

def administrativo(request):
    return render(request, 'menuadm.html')

def  sushi(request):
    sushi = Categoria.objects.get(nome='Sushi')
    produtos = Produto.objects.filter(categoria=sushi)
    return render(request, "sushi.html", {'produtos':produtos})
