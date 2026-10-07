from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError

CAMPOS_OPCIONAIS = ('nome', 'telefone', 'email', 'cep', 'numero', 'compl')


class CadastroClienteForm(forms.Form):
    """Cadastro pensado para testes e apresentações: só usuário e senha são obrigatórios.

    Nome, telefone, e-mail e endereço continuam disponíveis, mas opcionais. A senha aceita valores
    simples (mínimo de 4 caracteres); as regras de AUTH_PASSWORD_VALIDATORS seguem valendo no
    Django Admin e no createsuperuser.
    """
    username = forms.CharField(max_length=150, validators=[UnicodeUsernameValidator()], label='Usuário')
    password = forms.CharField(
        min_length=4, strip=False, widget=forms.PasswordInput, label='Senha',
        error_messages={'min_length': 'A senha precisa ter pelo menos 4 caracteres.'},
    )

    # ---- opcionais ----
    nome = forms.CharField(max_length=100, required=False)
    telefone = forms.CharField(max_length=16, required=False)
    email = forms.EmailField(required=False, label='E-mail')
    cep = forms.RegexField(r'^\d{5}-?\d{3}$', max_length=9, required=False,
                           error_messages={'invalid': 'Informe um CEP válido (ex.: 21240-430).'})
    numero = forms.IntegerField(min_value=0, max_value=999999, required=False, label='Número')
    compl = forms.CharField(max_length=28, required=False, label='Complemento')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username
