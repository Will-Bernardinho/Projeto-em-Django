import re

import requests
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.core.cache import cache
from django.db import IntegrityError, transaction
from django.shortcuts import render, redirect
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from cliente.forms import CadastroClienteForm, CAMPOS_OPCIONAIS
from cliente.models import garantir_cliente

# Proteção contra tentativas de adivinhar senhas
LOGIN_MAX_FALHAS = 5
LOGIN_JANELA_SEGUNDOS = 15 * 60


def _consulta_cep(cep):
    """Consulta o ViaCEP. Devolve um dict de endereço ou {'erro': mensagem}."""
    cep = (cep or '').strip()
    if not re.fullmatch(r'\d{5}-?\d{3}', cep):  # formato exato: nada digitado vira caminho ou consulta na URL
        return {'erro': 'Informe um CEP válido (ex.: 21240-430).'}
    digitos = cep.replace('-', '')
    try:
        resposta = requests.get(f'https://viacep.com.br/ws/{digitos}/json/', timeout=5)
        if resposta.status_code != 200:
            return {'erro': 'Erro ao buscar o endereço.'}
        endereco = resposta.json()
    except (requests.RequestException, ValueError):
        return {'erro': 'Não foi possível consultar o CEP agora. Tente novamente.'}
    if not isinstance(endereco, dict) or 'erro' in endereco:
        return {'erro': 'CEP não encontrado.'}
    return endereco


def _renderiza_cadastro(request, form, endereco=None):
    """A seção de dados opcionais abre sozinha quando há algo preenchido, com erro ou com endereço."""
    abrir = bool(endereco) or any(
        (form.data.get(c) if form.is_bound else form.initial.get(c)) for c in CAMPOS_OPCIONAIS)
    return render(request, 'cadastro_cliente.html', {'form': form, 'endereco': endereco or {}, 'abrir_opcionais': abrir})


def busca_cep(request):
    """Preenche o endereço pelo CEP sem cadastrar ninguém (mantém o que já foi digitado)."""
    endereco = {}
    inicial = {}
    if request.method == 'POST':
        inicial = {c: request.POST.get(c, '') for c in ('username', *CAMPOS_OPCIONAIS)}
        if inicial['cep']:
            endereco = _consulta_cep(inicial['cep'])
    return _renderiza_cadastro(request, CadastroClienteForm(initial=inicial), endereco)


def cadastrar_cliente(request):
    """Cadastro simples: só usuário e senha são obrigatórios; contato e endereço são opcionais."""
    if request.method != 'POST':
        return _renderiza_cadastro(request, CadastroClienteForm())

    form = CadastroClienteForm(request.POST)
    if form.is_valid():
        d = form.cleaned_data
        try:
            with transaction.atomic():  # ou cria usuário e cliente, ou nenhum dos dois
                usuario = User.objects.create_user(username=d['username'], password=d['password'], email=d['email'])
                garantir_cliente(usuario, **{c: d[c] for c in CAMPOS_OPCIONAIS if c != 'email'})
        except IntegrityError:
            form.add_error('username', 'Este nome de usuário já está em uso.')
        else:
            login(request, usuario)
            messages.success(request, 'Conta criada com sucesso. Bem-vindo!')
            return redirect('home')
    return _renderiza_cadastro(request, form)


def _destino_seguro(request, padrao='home'):
    proximo = request.POST.get('next') or request.GET.get('next') or ''
    if proximo and url_has_allowed_host_and_scheme(proximo, allowed_hosts={request.get_host()},
                                                   require_https=request.is_secure()):
        return proximo
    return padrao


def logar(request):
    proximo = request.POST.get('next') or request.GET.get('next') or ''
    contexto = {'next': proximo}

    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        chave = f"login:{request.META.get('REMOTE_ADDR', '')}:{username.lower()}"
        falhas = cache.get(chave, 0)

        if falhas >= LOGIN_MAX_FALHAS:
            contexto['erro'] = 'Muitas tentativas. Aguarde alguns minutos e tente de novo.'
            return render(request, 'login.html', contexto, status=429)

        user = authenticate(request, username=username, password=password)
        if user is not None:
            cache.delete(chave)
            login(request, user)

            # MOSTRAR A SESSÃO DE USUÁRIO (comportamento do projeto original)
            request.session['username'] = user.username

            messages.success(request, 'Bem-vindo!')
            return redirect(_destino_seguro(request))

        cache.set(chave, falhas + 1, LOGIN_JANELA_SEGUNDOS)
        contexto['erro'] = 'Usuário ou senha inválidos.'

    return render(request, 'login.html', contexto)


@require_POST
def sair(request):
    logout(request)
    return redirect('home')
