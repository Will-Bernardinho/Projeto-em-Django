from django.http import HttpResponse
from django.shortcuts import render, redirect

# Create your views here.
from .models import Cliente
import requests

def busca_cep(request):
    endereco = {}
    if request.method == 'POST':
        cep = request.POST.get('cep')
        url = f"https://viacep.com.br/ws/{cep}/json/"
        response = requests.get(url)
def cadastrar_cliente(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        cep = request.POST.get('cep')
        numero = request.POST.get('numero')
        compl = request.POST.get('compl')

        if nome and telefone and email and cep and numero and compl:
            cliente = Cliente(nome=nome, telefone=telefone, email=email, cep=cep, numero=numero, compl=compl)
            cliente.save()
            return redirect ('cadastro_cliente.html')

    return render(request, 'cadastro_cliente.html')

