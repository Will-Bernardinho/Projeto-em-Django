from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.urls import reverse


def staff_required(view):
    """Só funcionários (is_staff). Anônimo vai para o login; cliente comum recebe 403."""
    @wraps(view)
    def interna(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect_to_login(request.get_full_path(), reverse('logar'))
        if not request.user.is_staff:
            raise PermissionDenied
        return view(request, *args, **kwargs)
    return interna
