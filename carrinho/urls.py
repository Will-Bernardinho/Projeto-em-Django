from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from .views import addcarrinho, mostracarrinho

urlpatterns = [

                  path('addcarrinho/<int:produto_id>/', addcarrinho, name='addcarrinho'),
                  path('mostracarrinho', mostracarrinho, name='mostracarrinho'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)