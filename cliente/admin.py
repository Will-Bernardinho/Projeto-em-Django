from django import forms
from django.contrib import admin

from cliente.models import Cliente


class ClienteAdminForm(forms.ModelForm):
    """No admin, os dados de contato e endereço são opcionais (o cadastro só exige usuário e senha)."""

    class Meta:
        model = Cliente
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in ('nome', 'telefone', 'email', 'cep', 'numero', 'compl'):
            self.fields[campo].required = False

    def clean_numero(self):
        return self.cleaned_data.get('numero') or 0  # a coluna não aceita NULL


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    form = ClienteAdminForm
    list_display = ('nome', 'usuario', 'email')
