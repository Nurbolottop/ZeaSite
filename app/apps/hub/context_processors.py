from apps.users.access import get_user_roles
from apps.users.profile import get_hub_profile

from .middleware import HUB_URL_PREFIX
from .navigation import build_menu


def navigation(request):
    """Контекст layout Hub. На страницах публичного сайта ничего не делает."""
    if not request.path_info.startswith(HUB_URL_PREFIX):
        return {}
    user = getattr(request, 'user', None)
    if user is None or not user.is_authenticated:
        return {}
    match = getattr(request, 'resolver_match', None)
    return {
        'nav_menu': build_menu(user, match.view_name if match else None),
        'current_roles': get_user_roles(user),
        'hub_profile': get_hub_profile(user),
    }
