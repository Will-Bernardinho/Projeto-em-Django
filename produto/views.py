from django.shortcuts import render

# Create your views here.

def cadastrar(request):
    categorias = Categoria.objects.all()
    if request.method == 'POST':
        nome = request.POST.get('nome')
        descricao = request.POST.get('descricao')
        quantidade = request.POST.get('quant')
        preco = request.POST.get('preco')
        imagem = request.FILES.get('imagem')
        categoria_id = request.POST.get('categoria')

        if nome and descricao and quantidade and preco and imagem and categoria_id:
            categoria = Categoria.objects.get(id=categoria_id)
            produto = Produto(nome=nome, descricao=descricao, imagem=imagem, valor=preco, quantidade=quantidade, categoria=categoria)
            produto.save()
            return redirect('cadproduto.html')


    return render(request, 'cadproduto.html', {'categorias': categorias})
