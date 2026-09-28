from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied

from .access import can_access_module, has_role
from .mixins import DENIED_MESSAGE


def role_required(*roles, module=None):
    """Аналог RoleRequiredMixin для function-based view.

        @role_required(module='finance')
        @role_required(Role.HEAD, Role.PM)
    """

    def decorator(view):
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            user = request.user
            if not user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if module is not None and not can_access_module(user, module):
                raise PermissionDenied(DENIED_MESSAGE)
            if roles and not has_role(user, *roles):
                raise PermissionDenied(DENIED_MESSAGE)
            return view(request, *args, **kwargs)
        return wrapper

    return decorator
