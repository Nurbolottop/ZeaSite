from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.conf import settings as dj_settings
from apps.cms.models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings
)
from apps.contacts.forms import ContactForm


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
        'Disallow: /ckeditor/',
        'Disallow: /i18n/',
        '',
        f'Sitemap: {base_url}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
