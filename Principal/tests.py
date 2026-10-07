from pathlib import Path

from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.db import connection
from django.urls import reverse
from PIL import Image

from Principal.ajuda_testes import MidiaTemporaria, arquivo_imagem
from Principal.templatetags.imagens import miniatura
from categoria.models import Categoria
from produto.models import Produto

PAGINAS_PUBLICAS = ['home', 'historia', 'sushi', 'sashimi', 'temaki', 'sobremesas', 'bebidas', 'contato',
                    'logar', 'cadastrar_cliente', 'mostracarrinho']


class PaginasPublicasTests(TestCase):
    def test_paginas_abrem_mesmo_sem_nenhum_dado(self):
        """Banco vazio (sem categorias nem produtos) não pode gerar erro 500."""
        for nome in PAGINAS_PUBLICAS:
            with self.subTest(pagina=nome):
                self.assertEqual(self.client.get(reverse(nome)).status_code, 200)

    def test_categoria_removida_nao_quebra_a_pagina(self):
        Categoria.objects.create(nome='Sushi').delete()
        self.assertEqual(self.client.get(reverse('sushi')).status_code, 200)

    def test_categoria_sem_produtos_mostra_aviso(self):
        Categoria.objects.create(nome='Sashimi')
        self.assertContains(self.client.get(reverse('sashimi')), 'Em breve')


class HomeTests(MidiaTemporaria, TestCase):
    @classmethod
    def setUpTestData(cls):
        for nome in ['Sushi', 'Sashimi', 'Temaki', 'Sobremesas', 'Bebidas']:
            categoria = Categoria.objects.create(nome=nome)
            for i in range(3):
                Produto.objects.create(nome=f'{nome} {i}', descricao='d', valor='10.00', quantidade=5,
                                       categoria=categoria, imagem=arquivo_imagem(f'{nome}{i}.jpg'))

    def test_home_faz_poucas_consultas(self):
        """Antes eram ~17 consultas; agora o total não cresce com o número de categorias/produtos."""
        with CaptureQueriesContext(connection) as consultas:
            resposta = self.client.get(reverse('home'))
        self.assertEqual(resposta.status_code, 200)
        self.assertLessEqual(len(consultas), 3, [c['sql'][:80] for c in consultas])

    def test_home_lista_as_cinco_categorias_com_contagem(self):
        html = self.client.get(reverse('home')).content.decode()
        for nome in ['Sushi', 'Sashimi', 'Temaki', 'Sobremesas', 'Bebidas']:
            self.assertIn(nome, html)
        self.assertIn('3 pratos', html)

    def test_botao_adicionar_e_post_com_csrf(self):
        html = self.client.get(reverse('home')).content.decode()
        self.assertIn('csrfmiddlewaretoken', html)
        self.assertNotIn('href="/addcarrinho/', html)  # não existe mais link GET que altera estado

    def test_cdn_usa_sri(self):
        html = self.client.get(reverse('home')).content.decode()
        self.assertIn('integrity="sha384-', html)


class AcessoAdministrativoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.cliente = User.objects.create_user('cliente', password='Senha-forte-123')
        cls.staff = User.objects.create_user('func', password='Senha-forte-123', is_staff=True)

    def test_anonimo_vai_para_o_login(self):
        resposta = self.client.get(reverse('administrativo'))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse('logar')))
        self.assertIn('next=', resposta.url)

    def test_cliente_comum_recebe_403(self):
        self.client.force_login(self.cliente)
        self.assertEqual(self.client.get(reverse('administrativo')).status_code, 403)

    def test_funcionario_acessa(self):
        self.client.force_login(self.staff)
        self.assertEqual(self.client.get(reverse('administrativo')).status_code, 200)

    def test_link_adm_so_aparece_para_funcionario(self):
        self.assertNotContains(self.client.get(reverse('home')), reverse('administrativo'))
        self.client.force_login(self.cliente)
        self.assertNotContains(self.client.get(reverse('home')), reverse('administrativo'))
        self.client.force_login(self.staff)
        self.assertContains(self.client.get(reverse('home')), reverse('administrativo'))


class CategoriaTests(TestCase):
    def test_nome_da_categoria_e_unico(self):
        Categoria.objects.create(nome='Sushi')
        with self.assertRaises(IntegrityError), transaction.atomic():
            Categoria.objects.create(nome='Sushi')

    def test_str_devolve_o_nome(self):
        self.assertEqual(str(Categoria(nome='Temaki')), 'Temaki')


class MiniaturaTests(MidiaTemporaria, TestCase):
    def _produto(self, tamanho):
        categoria = Categoria.objects.create(nome='Sushi')
        return Produto.objects.create(nome='x', descricao='d', valor='1', quantidade=1, categoria=categoria,
                                      imagem=arquivo_imagem('grande.jpg', tamanho=tamanho))

    def test_gera_miniatura_menor_sem_tocar_na_original(self):
        produto = self._produto((1600, 1000))
        original = Path(produto.imagem.path)
        tamanho_original = original.stat().st_size

        url = miniatura(produto.imagem, 800)

        self.assertIn('/miniaturas/', url)
        self.assertTrue(url.endswith('_800.jpg'))
        arquivo = Path(produto.imagem.storage.location) / 'produtos' / 'miniaturas' / Path(url).name
        self.assertTrue(arquivo.exists())
        with Image.open(arquivo) as img:
            self.assertEqual(img.width, 800)
            self.assertEqual(img.height, 500)  # mantém a proporção
        self.assertEqual(original.stat().st_size, tamanho_original)  # original intacta

    def test_nao_amplia_imagem_pequena(self):
        produto = self._produto((300, 200))
        self.assertNotIn('/miniaturas/', miniatura(produto.imagem, 800))

    def test_arquivo_inexistente_nao_levanta_erro(self):
        self.assertEqual(miniatura('produtos/nao_existe.jpg', 800), '/media/produtos/nao_existe.jpg')
        self.assertEqual(miniatura('', 800), '')
        self.assertEqual(miniatura(None, 800), '')

    def test_segunda_chamada_reaproveita_o_arquivo(self):
        produto = self._produto((1600, 1000))
        primeira = miniatura(produto.imagem, 800)
        alvo = Path(produto.imagem.storage.location) / 'produtos' / 'miniaturas' / Path(primeira).name
        momento = alvo.stat().st_mtime_ns
        self.assertEqual(miniatura(produto.imagem, 800), primeira)
        self.assertEqual(alvo.stat().st_mtime_ns, momento)
