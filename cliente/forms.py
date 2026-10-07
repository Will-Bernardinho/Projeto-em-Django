from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError


class CadastroClienteForm(forms.Form):
    username = forms.CharField(max_length=150, validators=[UnicodeUsernameValidator()], label='Usuário')
    password = forms.CharField(widget=forms.PasswordInput, strip=False, label='Senha')
    nome = forms.CharField(max_length=100)
    telefone = forms.CharField(max_length=16)
    email = forms.EmailField()
    cep = forms.RegexField(r'^\d{5}-?\d{3}$', max_length=9, error_messages={'invalid': 'Informe um CEP válido (ex.: 21240-430).'})
    numero = forms.IntegerField(min_value=1, max_value=999999, label='Número')
    compl = forms.CharField(max_length=28, required=False, label='Complemento')

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username__iexact=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean(self):
        dados = super().clean()
        senha = dados.get('password')
        if senha:
            try:
                validate_password(senha, user=User(username=dados.get('username', ''), email=dados.get('email', '')))
            except ValidationError as erro:
                self.add_error('password', erro)
        return dados
