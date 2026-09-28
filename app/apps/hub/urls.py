from django.contrib.auth import views as auth_views
from django.urls import path

from apps.users.forms import LoginForm

from . import views
from .navigation import NAVIGATION

app_name = 'hub'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path(
        'login/',
        auth_views.LoginView.as_view(
            template_name='hub/login.html',
            authentication_form=LoginForm,
            redirect_authenticated_user=True,
        ),
        name='login',
    ),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
]

# Заглушки разделов в разработке. Когда модуль готов, его urls подключаются
# в core/urls.py как path('hub/<module>/', include(..., namespace=...)),
# а в NAVIGATION ставится ready=True и новый url_name.
urlpatterns += [
    path(f'{item.module}/', views.ModulePlaceholderView.as_view(module=item.module), name=item.module)
    for item in NAVIGATION
    if not item.ready
]
