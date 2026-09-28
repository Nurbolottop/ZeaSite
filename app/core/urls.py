"""URL configuration for core project."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap

from apps.base.views import robots_txt
from apps.partners.urls import candidate_patterns, partner_patterns
from apps.base.sitemaps import StaticViewSitemap

# ── Заголовки админки ──
admin.site.site_header = 'ZEA — Панель управления'
admin.site.site_title  = 'ZEA Admin'
admin.site.index_title = 'Управление сайтом'

handler403 = 'apps.hub.views.permission_denied'

sitemaps = {
    'static': StaticViewSitemap,
}

# ── Маршруты БЕЗ языкового префикса ──
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path('ckeditor/', include('ckeditor_uploader.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path('', include('apps.contacts.urls')),

    # ZEA Hub — внутренняя система. Все внутренние URL только под /hub/
    # (HubLoginRequiredMiddleware закрывает этот префикс целиком).
    path('hub/candidates/', include(candidate_patterns)),
    path('hub/partners/', include(partner_patterns)),
    path('hub/contracts/', include('apps.contracts.urls')),
    path('hub/projects/', include('apps.projects.urls')),
    path('hub/team/', include('apps.team.urls')),
    path('hub/', include('apps.hub.urls')),
]

# ── Маршруты С языковым префиксом (/ для ru, /ky/, /en/) ──
urlpatterns += i18n_patterns(
    path('', include('apps.base.urls')),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
