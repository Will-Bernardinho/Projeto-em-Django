import requests
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.shortcuts import render, redirect

from cliente.models import Cliente


def busca_cep(request):
    endereco = {}

    if request.method == 'POST':

        cep = request.POST.get('cep')
        if cep:
            url = f"https://viacep.com.br/ws/{cep}/json/"
            response = requests.get(url)

            if response.status_code == 200:
                endereco = response.json()
                if 'erro' in endereco:
                    endereco = {'erro': 'CEP não encontrado.'}
            else:
                endereco = {'erro': 'Erro ao buscar o endereço.'}


    nome = request.POST.get('nome', '')
    telefone = request.POST.get('telefone', '')
    email = request.POST.get('email', '')
    numero = request.POST.get('numero', '')
    compl = request.POST.get('compl', '')

    return render(request, 'cadastro_cliente.html', {
        'endereco': endereco,
        'nome': nome,
        'telefone': telefone,
        'email': email,
        'numero': numero,
        'compl': compl,
    })






def cadastrar_cliente(request):
    if request.method == 'POST':
            username = request.POST['username']
            password = request.POST['password']
            nome = request.POST.get('nome')
            telefone = request.POST.get('telefone')
            email = request.POST.get('email')
            cep = request.POST.get('cep')
            numero = request.POST.get('numero')
            compl = request.POST.get('compl')
            if username and nome and telefone and email and cep and numero and compl:
                usuario = User.objects.create_user(username=username, password=password, email=email)

                cliente = Cliente(
                    usuario=usuario,
                    nome=nome,
                    telefone=telefone,
                    email=email,
                    cep=cep,
                    numero=numero,
                    compl=compl
                )
                cliente.save()
                messages.success(request, 'cliente cadastrado com sucesso!')
                return redirect('administrativo')

    return busca_cep(request)

def logar(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            #MOSTRAR A SESSÃO DE USUÁRIO
            request.session['username'] = user.username

            messages.success(request, 'Bem vindo!')
            return redirect('menucli')  # Redireciona para a página de administrador
        else:
            return render(request, 'login.html')
    return render(request, 'login.html')

