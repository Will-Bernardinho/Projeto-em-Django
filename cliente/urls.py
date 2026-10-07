from django.urls import path

from cliente.views import cadastrar_cliente, busca_cep, logar, sair

urlpatterns = [
    path('cadastrar_cliente/', cadastrar_cliente, name='cadastrar_cliente'),
    path('busca_cep/', busca_cep, name='busca_cep'),
    path('logar/', logar, name='logar'),
    path('sair/', sair, name='sair'),
]
