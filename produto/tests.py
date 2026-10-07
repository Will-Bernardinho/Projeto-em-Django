import os
from io import BytesIO

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse
from PIL import Image

from Principal.ajuda_testes import MidiaTemporaria, arquivo_imagem
from categoria.models import Categoria
from produto.models import Produto


class CadastroProdutoTests(MidiaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nome='Sushi')
        cls.cliente = User.objects.create_user('cliente', password='Senha-forte-123')
        cls.staff = User.objects.create_user('func', password='Senha-forte-123', is_staff=True)

    def _dados(self, **mudancas):
        dados = {'categoria': self.categoria.id, 'nome': 'Uramaki', 'descricao': 'Salmão e cream cheese',
                 'quant': '10', 'preco': '24.90', 'imagem': arquivo_imagem('uramaki.jpg')}
        dados.update(mudancas)
        return dados

    def _enviar(self, **mudancas):
        return self.client.post(reverse('cadastrar_produto'), self._dados(**mudancas))

    # ---- controle de acesso (a falha mais grave encontrada na auditoria) ----

    def test_anonimo_nao_acessa_nem_envia(self):
        self.assertEqual(self.client.get(reverse('cadastrar_produto')).status_code, 302)
        resposta = self._enviar()
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse('logar')))
        self.assertEqual(Produto.objects.count(), 0)

    def test_cliente_comum_recebe_403_e_nada_e_criado(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('cadastrar_produto')).status_code, 403)
        self.assertEqual(self._enviar().status_code, 403)
        self.assertEqual(Produto.objects.count(), 0)

    # ---- uso normal ----

    def test_funcionario_cadastra_produto(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('cadastrar_produto')).status_code, 200)
        resposta = self._enviar()
        self.assertRedirects(resposta, reverse('cadastrar_produto'), fetch_redirect_response=False)
        produto = Produto.objects.get()
        self.assertEqual((produto.nome, str(produto.valor), produto.quantidade), ('Uramaki', '24.90', 10))
        self.assertTrue(produto.imagem.name.startswith('produtos/'))
        self.assertTrue(os.path.exists(produto.imagem.path))

    def test_aceita_png_e_webp(self):
        self.client.force_login(self.staff)
        self._enviar(imagem=arquivo_imagem('a.png', 'PNG', (50, 50)))
        self._enviar(nome='Outro', imagem=arquivo_imagem('b.webp', 'WEBP', (50, 50)))
        self.assertEqual(Produto.objects.count(), 2)

    # ---- upload malicioso / dados inválidos ----

    def test_arquivo_que_nao_e_imagem_e_recusado_mesmo_com_extensao_jpg(self):
        self.client.force_login(self.staff)
        falso = SimpleUploadedFile('foto.jpg', b'<?php system($_GET["c"]); ?>', content_type='image/jpeg')
        resposta = self._enviar(imagem=falso)
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(Produto.objects.count(), 0)

    def test_html_e_svg_disfarçados_de_imagem_sao_recusados(self):
        self.client.force_login(self.staff)
        for nome, conteudo, tipo in [('x.html', b'<script>alert(1)</script>', 'text/html'),
                                     ('x.svg', b'<svg onload="alert(1)"/>', 'image/svg+xml')]:
            with self.subTest(arquivo=nome):
                self._enviar(imagem=SimpleUploadedFile(nome, conteudo, content_type=tipo))
        self.assertEqual(Produto.objects.count(), 0)

    def test_formato_nao_permitido_e_recusado(self):
        self.client.force_login(self.staff)
        resposta = self._enviar(imagem=arquivo_imagem('a.gif', 'GIF', (20, 20)))
        self.assertContains(resposta, 'JPEG, PNG ou WEBP')
        self.assertEqual(Produto.objects.count(), 0)

    def test_imagem_acima_de_5mb_e_recusada(self):
        self.client.force_login(self.staff)
        buffer = BytesIO()
        Image.frombytes('RGB', (1800, 1800), os.urandom(1800 * 1800 * 3)).save(buffer, 'PNG')
        grande = SimpleUploadedFile('grande.png', buffer.getvalue(), content_type='image/png')
        self.assertGreater(grande.size, 5 * 1024 * 1024)
        resposta = self._enviar(imagem=grande)
        self.assertContains(resposta, 'no máximo 5 MB')
        self.assertEqual(Produto.objects.count(), 0)

    def test_valores_invalidos_sao_recusados(self):
        self.client.force_login(self.staff)
        casos = [{'preco': '0'}, {'preco': '-5'}, {'preco': 'abc'}, {'preco': '12.345'}, {'quant': '-1'},
                 {'quant': 'x'}, {'nome': ''}, {'nome': 'a' * 101}, {'categoria': '9999'}, {'categoria': ''},
                 {'categoria': 'DROP TABLE'}]
        for mudanca in casos:
            with self.subTest(**mudanca):
                resposta = self._enviar(**mudanca)
                self.assertEqual(resposta.status_code, 200)  # reexibe o formulário com erros, sem 500
        self.assertEqual(Produto.objects.count(), 0)

    def test_sem_imagem_e_recusado(self):
        self.client.force_login(self.staff)
        dados = self._dados()
        del dados['imagem']
        self.assertEqual(self.client.post(reverse('cadastrar_produto'), dados).status_code, 200)
        self.assertEqual(Produto.objects.count(), 0)

    def test_erros_aparecem_e_valores_digitados_sao_mantidos(self):
        self.client.force_login(self.staff)
        resposta = self._enviar(preco='-5')
        self.assertContains(resposta, 'erro-campo')
        self.assertContains(resposta, 'value="Uramaki"')

    def test_nome_com_html_e_escapado_na_listagem(self):
        self.client.force_login(self.staff)
        self._enviar(nome='<b>x</b>')
        html = self.client.get(reverse('sushi')).content.decode()
        self.assertNotIn('<b>x</b>', html)
        self.assertIn('&lt;b&gt;x&lt;/b&gt;', html)

    def test_csrf_e_exigido(self):
        estrito = Client(enforce_csrf_checks=True)
        estrito.force_login(self.staff)
        self.assertEqual(estrito.post(reverse('cadastrar_produto'), self._dados()).status_code, 403)


class ProdutoModelTests(TestCase):
    def test_estoque_nao_aceita_negativo(self):
        from django.db import IntegrityError, transaction
        categoria = Categoria.objects.create(nome='Sushi')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Produto.objects.create(nome='x', descricao='d', valor=1, quantidade=-1, categoria=categoria,
                                   imagem='produtos/x.jpg')
