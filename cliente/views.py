from django.http import HttpResponse
from django.shortcuts import render

# Create your views here.
from models import Cliente

def cadastrar_cliente(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        telefone = request.POST.get('telefone')
        email = request.POST.get('email')
        cliente = Cliente(codcli, nome, telefone)
        return HttpResponse(
            f"Cliente cadastrado com sucesso! <br> "
            f"Nome: {cliente.nome}"      
            f"<br> Telefone: {cliente.telefone}"
            f"<br> Email: {cliente.email}"
        )
        return render(request, 'cadastro_cliente.html')