from django.shortcuts import render

# Create your views here.
def inicio(request):
    return render(request, template_name='home.html')

def historia (request):
    return render(request, 'historia.html')