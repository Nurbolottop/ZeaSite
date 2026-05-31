from urllib.parse import urlparse
from django.contrib.sitemaps import Sitemap
from django.urls import reverse


class _DomainShim:
    """Подменяет объект Site доменом из настроек сайта."""
    def __init__(self, domain):
        self.domain = domain
        self.name = domain


class StaticViewSitemap(Sitemap):
    """Карта сайта для главной страницы на всех языках (ru/ky/en).

    i18n + alternates → Django добавляет <xhtml:link rel="alternate"
    hreflang="..."> для каждого языка автоматически.
    Домен берётся из SiteSettings.site_domain, иначе из хоста запроса.
    """
    priority   = 1.0
    changefreq = 'weekly'
    i18n       = True
    alternates = True

    def items(self):
        return ['index']

    def location(self, item):
        return reverse(item)

    def get_urls(self, page=1, site=None, protocol=None):
        from apps.cms.models import SiteSettings
        s = SiteSettings.objects.first()
        if s and s.site_domain:
            parsed = urlparse(s.site_domain)
            protocol = parsed.scheme or 'https'
            site = _DomainShim(parsed.netloc)
        return super().get_urls(page=page, site=site, protocol=protocol)
