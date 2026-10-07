"""Miniaturas sob demanda: {{ produto.imagem|miniatura:800 }}

Gera (uma única vez) uma cópia JPEG com a largura pedida em <pasta>/miniaturas/ e devolve a URL dela.
As imagens originais nunca são alteradas. Se algo falhar, devolve a URL da original.
"""
import os
from pathlib import Path
from urllib.parse import quote

from django import template
from django.conf import settings
from PIL import Image, ImageOps

register = template.Library()


def _url(caminho_relativo):
    return settings.MEDIA_URL + quote(Path(caminho_relativo).as_posix())


@register.filter
def miniatura(arquivo, largura=800):
    nome = getattr(arquivo, 'name', arquivo) or ''
    if not nome:
        return ''
    try:
        largura = int(largura)
        raiz = Path(settings.MEDIA_ROOT)
        origem = raiz / nome
        relativo = Path(nome).parent / 'miniaturas' / f'{Path(nome).stem}_{largura}.jpg'
        destino = raiz / relativo

        if destino.exists() and destino.stat().st_mtime >= origem.stat().st_mtime:
            return _url(relativo)

        with Image.open(origem) as img:
            img = ImageOps.exif_transpose(img)
            if img.width <= largura:  # já é pequena: não amplia
                return _url(nome)
            img = img.convert('RGB')
            img.thumbnail((largura, 100_000), Image.LANCZOS)
            destino.parent.mkdir(parents=True, exist_ok=True)
            temporario = destino.with_suffix('.tmp')
            img.save(temporario, format='JPEG', quality=85, optimize=True, progressive=True)
            os.replace(temporario, destino)  # troca atômica: nunca serve arquivo pela metade
        return _url(relativo)
    except Exception:
        return _url(nome)
