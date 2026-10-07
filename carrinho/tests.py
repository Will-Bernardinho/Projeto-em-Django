from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from carrinho.views import LIMITE_POR_ITEM
from categoria.models import Categoria
from cliente.models import Cliente
from itens_pedido.models import ItemPedido
from pedido.models import Pedido
from produto.models import Produto


class BaseCarrinho(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.categoria = Categoria.objects.create(nome='Sushi')
        cls.p1 = Produto.objects.create(nome='Nigiri', descricao='d', valor=Decimal('12.50'), quantidade=5,
                                        categoria=cls.categoria, imagem='produtos/x.jpg')
        cls.p2 = Produto.objects.create(nome='Temaki', descricao='d', valor=Decimal('30.00'), quantidade=5,
                                        categoria=cls.categoria, imagem='produtos/y.jpg')
        cls.usuario = User.objects.create_user('cli', password='Sushi-forte-2026')
        cls.cliente = Cliente.objects.create(usuario=cls.usuario, nome='Cli', telefone='1', email='c@x.com',
                                             cep='21240-430', numero=1, compl='')

    def adicionar(self, produto, vezes=1, **extra):
        for _ in range(vezes):
            resposta = self.client.post(reverse('addcarrinho', args=[produto.id]), **extra)
        return resposta


class AdicionarTests(BaseCarrinho):
    def test_adicionar_exige_post(self):
        """Antes era GET: bastava um <img src='/addcarrinho/1/'> em outro site para mexer no carrinho."""
        self.assertEqual(self.client.get(reverse('addcarrinho', args=[self.p1.id])).status_code, 405)
        self.assertEqual(self.client.session.get('carrinho', {}), {})

    def test_adicionar_sem_token_csrf_e_recusado(self):
        cliente_estrito = Client(enforce_csrf_checks=True)
        resposta = cliente_estrito.post(reverse('addcarrinho', args=[self.p1.id]))
        self.assertEqual(resposta.status_code, 403)

    def test_adicionar_incrementa_a_quantidade(self):
        self.adicionar(self.p1, 3)
        self.assertEqual(self.client.session['carrinho'], {str(self.p1.id): 3})

    def test_produto_inexistente_da_404(self):
        self.assertEqual(self.client.post(reverse('addcarrinho', args=[9999])).status_code, 404)

    def test_volta_para_a_pagina_de_origem(self):
        resposta = self.adicionar(self.p1, HTTP_REFERER='http://testserver/sushi/')
        self.assertEqual(resposta.url, 'http://testserver/sushi/')

    def test_referer_externo_e_ignorado(self):
        for referer in ['http://evil.example/x', 'https://evil.example', 'javascript:alert(1)']:
            with self.subTest(referer=referer):
                self.assertEqual(self.adicionar(self.p1, HTTP_REFERER=referer).url, reverse('home'))

    def test_limite_por_item(self):
        self.adicionar(self.p1, LIMITE_POR_ITEM + 5)
        self.assertEqual(self.client.session['carrinho'][str(self.p1.id)], LIMITE_POR_ITEM)


class RemoverTests(BaseCarrinho):
    def test_remover_exige_post(self):
        self.adicionar(self.p1)
        self.assertEqual(self.client.get(reverse('removercarrinho', args=[self.p1.id])).status_code, 405)
        self.assertIn(str(self.p1.id), self.client.session['carrinho'])

    def test_remover_tira_so_o_item_escolhido(self):
        self.adicionar(self.p1, 2)
        self.adicionar(self.p2)
        self.client.post(reverse('removercarrinho', args=[self.p2.id]))
        self.assertEqual(self.client.session['carrinho'], {str(self.p1.id): 2})

    def test_remover_item_que_nao_esta_no_carrinho_e_inofensivo(self):
        self.assertEqual(self.client.post(reverse('removercarrinho', args=[9999])).status_code, 302)


class MostrarCarrinhoTests(BaseCarrinho):
    def test_total_soma_quantidades(self):
        self.adicionar(self.p1, 2)
        self.adicionar(self.p2)
        resposta = self.client.get(reverse('mostracarrinho'))
        self.assertEqual(resposta.context['total'], Decimal('55.00'))
        self.assertContains(resposta, '55,00')

    def test_produto_apagado_do_banco_nao_derruba_a_pagina(self):
        """Antes: get_object_or_404 dentro do laço -> a página inteira virava 404 para sempre."""
        self.adicionar(self.p1)
        self.adicionar(self.p2)
        self.p2.delete()
        resposta = self.client.get(reverse('mostracarrinho'))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(self.client.session['carrinho'], {str(self.p1.id): 1})  # sessão é limpa

    def test_sessao_adulterada_e_ignorada(self):
        sessao = self.client.session
        sessao['carrinho'] = {'abc': 1, '1; DROP TABLE': 2, str(self.p1.id): 'muitos', str(self.p2.id): -5, '-1': 3}
        sessao.save()
        resposta = self.client.get(reverse('mostracarrinho'))
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.context['carrinho_itens'], [])

    def test_quantidade_enorme_na_sessao_e_limitada(self):
        sessao = self.client.session
        sessao['carrinho'] = {str(self.p1.id): 10**9}
        sessao.save()
        self.assertEqual(self.client.get(reverse('mostracarrinho')).context['carrinho_itens'][0]['quantidade'],
                         LIMITE_POR_ITEM)

    def test_numero_de_consultas_nao_cresce_com_os_itens(self):
        extras = [Produto.objects.create(nome=f'P{i}', descricao='d', valor='1', quantidade=1,
                                         categoria=self.categoria, imagem='produtos/z.jpg') for i in range(8)]
        for produto in [self.p1, self.p2, *extras]:
            self.adicionar(produto)
        with CaptureQueriesContext(connection) as consultas:
            self.client.get(reverse('mostracarrinho'))
        self.assertLessEqual(len(consultas), 3, [c['sql'][:80] for c in consultas])  # antes: 1 por item


class FinalizarCompraTests(BaseCarrinho):
    def test_exige_login(self):
        self.adicionar(self.p1)
        resposta = self.client.post(reverse('finalizar_compra'))
        self.assertEqual(resposta.status_code, 302)
        self.assertTrue(resposta.url.startswith(reverse('logar')))
        self.assertEqual(Pedido.objects.count(), 0)

    def test_exige_post(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.get(reverse('finalizar_compra')).status_code, 405)

    def test_cria_pedido_com_itens_e_total_e_esvazia_o_carrinho(self):
        self.client.force_login(self.usuario)
        self.adicionar(self.p1, 2)
        self.adicionar(self.p2)
        resposta = self.client.post(reverse('finalizar_compra'))
        self.assertRedirects(resposta, reverse('home'), fetch_redirect_response=False)

        pedido = Pedido.objects.get()
        self.assertEqual(pedido.cliente, self.cliente)
        self.assertEqual(pedido.valor_total, Decimal('55.00'))
        itens = {i.produto_id: (i.quantidade, i.valor_unitario) for i in ItemPedido.objects.filter(pedido=pedido)}
        self.assertEqual(itens, {self.p1.id: (2, Decimal('12.50')), self.p2.id: (1, Decimal('30.00'))})
        self.assertEqual(self.client.session['carrinho'], {})

    def test_preco_do_pedido_fica_congelado(self):
        self.client.force_login(self.usuario)
        self.adicionar(self.p1)
        self.client.post(reverse('finalizar_compra'))
        Produto.objects.filter(pk=self.p1.pk).update(valor=Decimal('99.00'))
        self.assertEqual(ItemPedido.objects.get().valor_unitario, Decimal('12.50'))

    def test_carrinho_vazio_nao_cria_pedido(self):
        self.client.force_login(self.usuario)
        self.assertEqual(self.client.post(reverse('finalizar_compra')).status_code, 302)
        self.assertEqual(Pedido.objects.count(), 0)

    def test_usuario_sem_cadastro_de_cliente_recebe_aviso_e_nao_erro_500(self):
        sem_cadastro = User.objects.create_user('sem', password='Sushi-forte-2026')
        self.client.force_login(sem_cadastro)
        self.adicionar(self.p1)
        resposta = self.client.post(reverse('finalizar_compra'), follow=True)
        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'não tem cadastro de cliente')
        self.assertEqual(Pedido.objects.count(), 0)

    def test_falha_no_meio_nao_deixa_pedido_pela_metade(self):
        self.client.force_login(self.usuario)
        self.adicionar(self.p1)
        with patch('carrinho.views.ItemPedido.objects.bulk_create', side_effect=RuntimeError('falha')):
            with self.assertRaises(RuntimeError):
                self.client.post(reverse('finalizar_compra'))
        self.assertEqual(Pedido.objects.count(), 0)  # transação revertida
        self.assertEqual(self.client.session['carrinho'], {str(self.p1.id): 1})  # carrinho preservado
