"""Utilitários compartilhados pelos testes do projeto."""
import shutil
import tempfile
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from PIL import Image


def arquivo_imagem(nome='foto.jpg', formato='JPEG', tamanho=(1600, 1000), cor=(200, 80, 60)):
    """Cria uma imagem de verdade, pronta para upload."""
    buffer = BytesIO()
    Image.new('RGB', tamanho, cor).save(buffer, formato)
    tipo = {'JPEG': 'image/jpeg', 'PNG': 'image/png', 'GIF': 'image/gif', 'WEBP': 'image/webp'}[formato]
    return SimpleUploadedFile(nome, buffer.getvalue(), content_type=tipo)


class MidiaTemporaria:
    """Mixin: os testes gravam uploads numa pasta temporária, nunca em app/media."""

    @classmethod
    def setUpClass(cls):
        cls._pasta_midia = tempfile.mkdtemp(prefix='sushibom_teste_')
        cls._override_midia = override_settings(MEDIA_ROOT=cls._pasta_midia)
        cls._override_midia.enable()
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls._override_midia.disable()
        shutil.rmtree(cls._pasta_midia, ignore_errors=True)
