from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import addcarrinho, mostracarrinho, finalizar_compra

urlpatterns = [

                  path('addcarrinho/<int:produto_id>/', addcarrinho, name='addcarrinho'),
                  path('mostracarrinho', mostracarrinho, name='mostracarrinho'),
                  path('finalizar_compra/', finalizar_compra, name='finalizar_compra'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)