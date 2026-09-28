import os
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.conf import settings as dj_settings
from apps.cms.models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings
)
from apps.contacts.forms import ContactForm


_TAILWIND_CSS = None


def _tailwind_inline():
    """Содержимое собранного tailwind.css для встраивания в <style> (убирает
    render-blocking запрос). Читается с диска один раз и кэшируется в памяти."""
    global _TAILWIND_CSS
    if _TAILWIND_CSS is None:
        path = os.path.join(dj_settings.STATIC_ROOT, 'css', 'tailwind.css')
        try:
            with open(path, encoding='utf-8') as fh:
                _TAILWIND_CSS = fh.read()
        except OSError:
            _TAILWIND_CSS = ''
    return _TAILWIND_CSS


def _alt_lang_urls(request, base_url):
    """URL текущей страницы для каждого языка (для hreflang / og:locale)."""
    urls = {}
    for code, _name in dj_settings.LANGUAGES:
        with translation.override(code):
            urls[code] = base_url + reverse('index')
    return urls


def index(request):
    site = SiteSettings.get()
    base_url = site.get_base_url(request)

    context = {
        'settings':      site,
        'tailwind_inline': _tailwind_inline(),
        'services':      Service.objects.filter(is_active=True),
        'projects':      Project.objects.filter(is_active=True),
        'partners':      Partner.objects.filter(is_active=True),
        'tech_stack':    TechStack.objects.filter(is_active=True),
        'why_us':        WhyUs.objects.filter(is_active=True),
        'stats':         Stat.objects.all(),
        'contact_form':  ContactForm(),
        # ── SEO ──
        'base_url':      base_url,
        'canonical_url': base_url + request.path,
        'alt_lang_urls': _alt_lang_urls(request, base_url),
    }
    return render(request, 'index.html', context)


def robots_txt(request):
    site = SiteSettings.objects.first()
    base_url = site.get_base_url(request) if site else f'{request.scheme}://{request.get_host()}'
    lines = [
        'User-agent: *',
        'Allow: /',
        'Disallow: /admin/',
        'Disallow: /hub/',
        'Disallow: /ckeditor/',
        'Disallow: /i18n/',
        '',
        f'Sitemap: {base_url}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
