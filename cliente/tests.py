from unittest.mock import MagicMock, patch

import requests
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from cliente.models import Cliente

DADOS_VALIDOS = {
    'username': 'maria', 'password': 'Sushi-forte-2026', 'nome': 'Maria Silva',
    'telefone': '(21) 99999-0000', 'email': 'maria@example.com',
    'cep': '21240-430', 'numero': '100', 'compl': 'Apto 2',
}


class CadastroClienteTests(TestCase):
    def setUp(self):
        cache.clear()

    def _cadastrar(self, **mudancas):
        return self.client.post(reverse('cadastrar_cliente'), {**DADOS_VALIDOS, **mudancas})

    def test_cadastro_valido_cria_usuario_e_cliente_e_ja_loga(self):
        resposta = self._cadastrar()
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)
        usuario = User.objects.get(username='maria')
        self.assertTrue(usuario.check_password('Sushi-forte-2026'))
        self.assertEqual(Cliente.objects.get(usuario=usuario).nome, 'Maria Silva')
        self.assertEqual(int(self.client.session['_auth_user_id']), usuario.pk)
        self.assertFalse(usuario.is_staff)  # cadastro público nunca cria funcionário

    def test_complemento_e_opcional(self):
        self._cadastrar(compl='')
        self.assertTrue(Cliente.objects.filter(usuario__username='maria').exists())

    def test_usuario_duplicado_mostra_erro_em_vez_de_500(self):
        User.objects.create_user('Maria', password='x')
        resposta = self._cadastrar()  # "maria" colide com "Maria" (sem diferenciar maiúsculas)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'já está em uso')
        self.assertEqual(User.objects.filter(username__iexact='maria').count(), 1)
        self.assertEqual(Cliente.objects.count(), 0)

    def test_senha_fraca_e_recusada(self):
        for senha in ['12345678', 'curta', 'password', 'maria1234']:
            with self.subTest(senha=senha):
                resposta = self._cadastrar(password=senha)
                self.assertEqual(resposta.status_code, 200)
                self.assertFalse(User.objects.filter(username='maria').exists())

    def test_campos_invalidos_nao_criam_nada(self):
        casos = {'cep': ['abc', '123', '../../etc'], 'email': ['sem-arroba'], 'numero': ['0', 'x', '-4'],
                 'nome': [''], 'telefone': ['1' * 40], 'username': ['com espaço', '<script>']}
        for campo, valores in casos.items():
            for valor in valores:
                with self.subTest(campo=campo, valor=valor):
                    resposta = self._cadastrar(**{campo: valor})
                    self.assertEqual(resposta.status_code, 200)
                    self.assertEqual(User.objects.count(), 0)

    def test_campo_ausente_nao_gera_500(self):
        dados = {k: v for k, v in DADOS_VALIDOS.items() if k != 'username'}
        self.assertEqual(self.client.post(reverse('cadastrar_cliente'), dados).status_code, 200)

    def test_falha_ao_salvar_cliente_desfaz_o_usuario(self):
        with patch('cliente.views.Cliente.objects.create', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                self._cadastrar()
        self.assertFalse(User.objects.filter(username='maria').exists())  # transação revertida

    def test_nome_com_html_e_escapado(self):
        resposta = self._cadastrar(nome='<script>alert(1)</script>', cep='x')
        self.assertNotContains(resposta, '<script>alert(1)</script>')


class BuscaCepTests(TestCase):
    def _post(self, **dados):
        return self.client.post(reverse('busca_cep'), {'cep': '21240-430', 'username': 'joao', **dados})

    def test_preenche_endereco_sem_cadastrar_ninguem(self):
        resposta_viacep = MagicMock(status_code=200)
        resposta_viacep.json.return_value = {'logradouro': 'Rua das Flores', 'bairro': 'Jardim América',
                                             'localidade': 'Rio de Janeiro', 'uf': 'RJ'}
        with patch('cliente.views.requests.get', return_value=resposta_viacep) as get:
            resposta = self._post(**DADOS_VALIDOS)
        self.assertContains(resposta, 'Rua das Flores')
        self.assertContains(resposta, 'value="maria"')  # mantém o que já foi digitado
        self.assertEqual(User.objects.count(), 0)  # "Buscar" nunca cadastra
        url = get.call_args.args[0]
        self.assertEqual(url, 'https://viacep.com.br/ws/21240430/json/')  # só dígitos na URL
        self.assertEqual(get.call_args.kwargs['timeout'], 5)

    def test_cep_malformado_nem_chega_a_consultar_o_servico(self):
        for cep in ['../../admin', '21240-430/../x', '12345', 'abcdefgh', '1234567890', '2124043?x=1']:
            with self.subTest(cep=cep), patch('cliente.views.requests.get') as get:
                resposta = self._post(cep=cep)
                get.assert_not_called()
                self.assertContains(resposta, 'CEP válido')

    def test_servico_fora_do_ar_mostra_mensagem(self):
        for erro in [requests.Timeout(), requests.ConnectionError()]:
            with self.subTest(erro=type(erro).__name__), patch('cliente.views.requests.get', side_effect=erro):
                resposta = self._post()
                self.assertEqual(resposta.status_code, 200)
                self.assertContains(resposta, 'Não foi possível consultar o CEP')

    def test_cep_inexistente_e_resposta_nao_json(self):
        inexistente = MagicMock(status_code=200)
        inexistente.json.return_value = {'erro': True}
        lixo = MagicMock(status_code=200)
        lixo.json.side_effect = ValueError('não é json')
        for resposta_falsa, texto in [(inexistente, 'CEP não encontrado'), (lixo, 'Não foi possível')]:
            with self.subTest(texto=texto), patch('cliente.views.requests.get', return_value=resposta_falsa):
                self.assertContains(self._post(), texto)


class LoginTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.usuario = User.objects.create_user('ana', password='Sushi-forte-2026')

    def setUp(self):
        cache.clear()

    def _login(self, senha='Sushi-forte-2026', **extra):
        return self.client.post(reverse('logar'), {'username': 'ana', 'password': senha, **extra})

    def test_login_valido(self):
        resposta = self._login()
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session['_auth_user_id']), self.usuario.pk)

    def test_login_invalido_nao_revela_qual_campo_errou(self):
        for dados in [{'username': 'ana', 'password': 'errada'}, {'username': 'ninguem', 'password': 'x'}]:
            with self.subTest(dados=dados):
                resposta = self.client.post(reverse('logar'), dados)
                self.assertContains(resposta, 'Usuário ou senha inválidos')

    def test_requisicao_sem_campos_nao_gera_500(self):
        self.assertEqual(self.client.post(reverse('logar'), {}).status_code, 200)

    def test_bloqueia_apos_cinco_tentativas_erradas(self):
        for _ in range(5):
            self.assertEqual(self._login('errada').status_code, 200)
        bloqueado = self._login('Sushi-forte-2026')  # até a senha certa é recusada durante o bloqueio
        self.assertEqual(bloqueado.status_code, 429)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_bloqueio_nao_afeta_outro_usuario(self):
        User.objects.create_user('bia', password='Outra-senha-2026')
        for _ in range(5):
            self._login('errada')
        resposta = self.client.post(reverse('logar'), {'username': 'bia', 'password': 'Outra-senha-2026'})
        self.assertEqual(resposta.status_code, 302)

    def test_login_correto_zera_o_contador(self):
        for _ in range(4):
            self._login('errada')
        self.assertEqual(self._login().status_code, 302)
        self.client.post(reverse('sair'))
        for _ in range(4):
            self._login('errada')
        self.assertEqual(self._login().status_code, 302)

    def test_next_interno_e_respeitado(self):
        self.assertRedirects(self._login(next='/mostracarrinho'), '/mostracarrinho', fetch_redirect_response=False)

    def test_next_externo_e_ignorado(self):
        for alvo in ['https://evil.example/', '//evil.example/', 'javascript:alert(1)', 'http://evil.example@localhost/']:
            with self.subTest(alvo=alvo):
                cache.clear()
                self.client.post(reverse('sair'))
                resposta = self._login(next=alvo)
                self.assertEqual(resposta.url, reverse('home'))

    def test_logout_exige_post(self):
        self._login()
        self.assertEqual(self.client.get(reverse('sair')).status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)
        self.assertEqual(self.client.post(reverse('sair')).status_code, 302)
        self.assertNotIn('_auth_user_id', self.client.session)
