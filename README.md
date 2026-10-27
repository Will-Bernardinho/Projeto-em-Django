<p align="center">
  <a href="https://github.com/anymagalhaes/Projeto-em-/Django-Compras">
    <img src="./Principal/static/principal/favicon/apple-touch-icon.png" alt="Logo SushiBom" width="160" height="160">
  </a>
</p>


# SushiBom 寿 - Jardim América

Site de pedidos de um restaurante de culinária japonesa, desenvolvido em **Django**. O cliente navega pelo site, olha o cardápio, monta o carrinho e finaliza o pedido.
## Funcionalidades

- Página inicial com capa, categorias, novidades e apresentação do restaurante;
- Cardápio por categoria: Sushi, Sashimi, Temaki, Sobremesas e Bebidas;
- Carrinho de compras com limite de 20 unidades por item;
- Cadastro e login de clientes, com proteção contra tentativas repetidas de senha;
- Consulta de endereço por CEP (API ViaCEP);
- Finalização de compra, gravando o pedido e seus itens no banco;
- Painel administrativo para a equipe: cadastro de produtos e clientes (Django admin);
- Miniaturas de imagem geradas automaticamente para o site carregar mais rápido;



## Como executar

Os comandos abaixo são para **Windows**. Em Linux/macOS, troque a ativação do ambiente virtual por `source venv/bin/activate`.

### 1. Obter o projeto

```bash
git clone https://github.com/Will-Bernardinho/Projeto-em-Django.git
```

Se recebeu o projeto em `.zip`, extraia e abra o terminal dentro da pasta onde está o `manage.py`.

### 2. Criar e ativar o ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

### 4. Preparar o banco de dados

O projeto já traz um `db.sqlite3` com categorias e produtos de exemplo. Para garantir que a estrutura está atualizada:

```bash
python manage.py migrate
```

### 5. Iniciar o servidor

```bash
python manage.py runserver
```

Acesse **http://127.0.0.1:8000/**.

## Endereços do site

| Endereço | O que é |
|----------|---------|
| `/` | Página inicial/Home |
| `/sushi/`, `/sashimi/`, `/temaki/`, `/sobremesas/`, `/bebidas/` | Cardápio por categoria |
| `/historia/` | Nossa história |
| `/contato/` | Contatos |
| `/mostracarrinho` | Carrinho |
| `/cadastrar_cliente/` | Criar conta |
| `/logar/` | Entrar |
| `/administrativo/` | Painel da equipe (só usuários da equipe) |
| `/cadastrar_produto/` | Cadastro de produto (só usuários da equipe) |
| `/admin/` | Django Admin |


## Estrutura do projeto

```
app/            configurações do Django e pasta de mídia (app/media)
Principal/      páginas do site, cardápio, templates, estilos e filtro de miniaturas
produto/        cadastro de produtos
categoria/      categorias do cardápio
cliente/        cadastro, login e dados dos clientes
carrinho/       carrinho de compras e finalização do pedido
pedido/         pedidos
itens_pedido/   itens de cada pedido
```


## Tecnologias

- Python
- Django
- Pillow (tratamento de imagens)
- Requests (consulta de CEP)
- SQLite (banco de dados)
- Bootstrap 5 (interface)


## Participantes

| Nome | Contato |
|------|---------|
| _William Bernardo_ | _[GitHub](https://github.com/Will-Bernardinho)_ |
| _Gabriel Novaes_ | _[GitHub](https://github.com/gabrielnovaesdev)_ |
| _Ingrid_ | _[GitHub](https://github.com/Indy-Hunnigan)_ |
| _Gabriel Henrique_ | _[GitHub](https://github.com/GabrielHenriquefs)_ |
| _Stefany Magalhães_ | _[GitHub](https://github.com/anymagalhaes)_ |


**Instituição / disciplina:** _Centro Universitário: Unicarioca - Projeto de Extensão em Software Fullstack_ <br>
**Professor(a):** _Marcelo Perantoni_ <br>
**Ano / semestre:** _2026 - Disciplina do 6º Período_ <br>
