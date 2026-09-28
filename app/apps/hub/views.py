from django.shortcuts import render
from django.views import defaults
from django.views.generic import TemplateView

from apps.users.mixins import DENIED_MESSAGE, RoleRequiredMixin

from .middleware import HUB_URL_PREFIX
from .navigation import NAV_BY_MODULE

# Карточки будущих показателей Dashboard (данные появятся с модулями)
DASHBOARD_CARDS = (
    {'title': 'Кандидаты в работе', 'icon': 'person-plus'},
    {'title': 'Активные партнёры',  'icon': 'building'},
    {'title': 'Проекты в работе',   'icon': 'kanban'},
    {'title': 'Выручка за месяц',   'icon': 'cash-stack'},
)


class DashboardView(RoleRequiredMixin, TemplateView):
    module = 'dashboard'
    template_name = 'hub/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cards'] = DASHBOARD_CARDS
        return context


def permission_denied(request, exception=None):
    """handler403: внутри Hub — страница в layout Hub, на сайте — стандартная."""
    if request.path_info.startswith(HUB_URL_PREFIX):
        message = str(exception) if exception and str(exception) else DENIED_MESSAGE
        return render(request, 'hub/403.html', {'message': message}, status=403)
    return defaults.permission_denied(request, exception)


class ModulePlaceholderView(RoleRequiredMixin, TemplateView):
    """Заглушка раздела, который ещё не разработан."""

    template_name = 'hub/placeholder.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nav_item'] = NAV_BY_MODULE[self.module]
        return context
