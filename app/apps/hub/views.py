from django.shortcuts import render
from django.views import defaults
from django.views.generic import TemplateView

from apps.contracts import selectors as contract_selectors
from apps.partners import selectors as partner_selectors
from apps.projects import selectors as project_selectors
from apps.users.access import can_access_module
from apps.users.mixins import DENIED_MESSAGE, RoleRequiredMixin

from .middleware import HUB_URL_PREFIX
from .navigation import NAV_BY_MODULE

# Показатели модулей, которые ещё не разработаны
FUTURE_CARDS = (
    {'title': 'Выручка за месяц', 'icon': 'cash-stack'},
)


class DashboardView(RoleRequiredMixin, TemplateView):
    module = 'dashboard'
    template_name = 'hub/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Цифры по кандидатам — только тем, кому открыт раздел
        if can_access_module(self.request.user, 'candidates'):
            context['partner_stats'] = partner_selectors.dashboard_stats()
        if can_access_module(self.request.user, 'projects'):
            context['project_stats'] = project_selectors.dashboard_stats(self.request.user)
        if can_access_module(self.request.user, 'contracts'):
            context['contract_stats'] = contract_selectors.dashboard_stats()
        context['future_cards'] = FUTURE_CARDS
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
