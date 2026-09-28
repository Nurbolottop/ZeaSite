from django.conf import settings
from django.contrib.auth.middleware import LoginRequiredMiddleware
from django.utils import translation

HUB_URL_PREFIX = '/hub/'


class HubLoginRequiredMiddleware(LoginRequiredMiddleware):
    """Требует авторизацию для ВСЕХ URL под /hub/, кроме помеченных @login_not_required.

    Публичный сайт (всё вне /hub/) middleware не затрагивает — закрыть его
    случайно нельзя. Внутри /hub/ действует default-deny: новый view
    защищён, даже если в нём забыли RoleRequiredMixin.
    Hub всегда работает на русском, независимо от языка сайта (cookie ky/en).
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.path_info.startswith(HUB_URL_PREFIX):
            return None
        translation.activate(settings.LANGUAGE_CODE)
        request.LANGUAGE_CODE = settings.LANGUAGE_CODE
        return super().process_view(request, view_func, view_args, view_kwargs)
