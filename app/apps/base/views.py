import json
import os
from django.shortcuts import render
from django.http import HttpResponse
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings as dj_settings
from django.contrib.staticfiles import finders
from apps.cms.models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings,
    CooperationFormat, ProcessStep, Commitment,
)
from apps.contacts.forms import ContactForm


TAILWIND_PATH = os.path.join('css', 'tailwind.css')
OG_LOCALES = {'ru': 'ru_RU', 'ky': 'ky_KG', 'en': 'en_US'}

_TAILWIND_CSS = None


def _tailwind_inline():
    """Собранный tailwind.css (app/static/css/tailwind.css, хранится в git)
    для встраивания в <style> — без render-blocking запроса.

    Сначала STATIC_ROOT (после collectstatic), затем исходник через finders —
    поэтому стили есть и на чистом clone без collectstatic. В DEBUG файл
    перечитывается на каждый запрос (удобно при `npm run watch:css`)."""
    global _TAILWIND_CSS
    if _TAILWIND_CSS is not None and not dj_settings.DEBUG:
        return _TAILWIND_CSS
    candidates = [finders.find(TAILWIND_PATH)] if dj_settings.DEBUG else []
    candidates += [os.path.join(dj_settings.STATIC_ROOT, TAILWIND_PATH), finders.find(TAILWIND_PATH)]
    css = ''
    for path in candidates:
        if not path:
            continue
        try:
            with open(path, encoding='utf-8') as fh:
                css = fh.read()
            break
        except OSError:
            continue
    _TAILWIND_CSS = css
    return css


def _alt_lang_urls(request, base_url):
    """URL текущей страницы для каждого языка (для hreflang / og:locale)."""
    urls = {}
    for code, _name in dj_settings.LANGUAGES:
        with translation.override(code):
            urls[code] = base_url + reverse('index')
    return urls


def _organization_jsonld(site, base_url, description):
    data = {
        '@context': 'https://schema.org',
        '@type': 'Organization',
        'name': site.site_name,
        'url': base_url + '/',
        'description': description,
    }
    if site.logo:
        data['logo'] = base_url + site.logo.url
    if site.email:
        data['email'] = site.email
    same_as = [u for u in (site.telegram_url, site.whatsapp_url, site.instagram_url) if u]
    if same_as:
        data['sameAs'] = same_as
    # «<» экранируется, чтобы текст из CMS не мог закрыть <script>.
    return json.dumps(data, ensure_ascii=False).replace('<', '\\u003c')


def index(request):
    site = SiteSettings.get()
    base_url = site.get_base_url(request)
    lang = translation.get_language()

    projects = list(Project.objects.filter(is_active=True).order_by('-is_featured', 'order'))
    partners = list(Partner.objects.filter(is_active=True))
    stats = list(Stat.objects.filter(is_active=True))

    nav_items = [('#about', _('О нас')), ('#cooperation', _('Сотрудничество')),
                 ('#services', _('Направления'))]
    if projects:
        nav_items.append(('#projects', _('Проекты')))
    nav_items.append(('#contact', _('Контакты')))

    meta_title = site.meta_title or f'{site.site_name} — {site.site_tagline}'
    meta_description = site.meta_description or site.hero_subtitle

    context = {
        'settings':        site,
        'tailwind_inline': _tailwind_inline(),
        'nav_items':       nav_items,
        'commitments':     Commitment.objects.filter(is_active=True),
        'formats':         CooperationFormat.objects.filter(is_active=True),
        'process_steps':   ProcessStep.objects.filter(is_active=True),
        'services':        Service.objects.filter(is_active=True),
        'projects':        projects,
        'hero_projects':   [p for p in projects if p.is_featured][:2],
        'partners':        partners,
        'tech_stack':      TechStack.objects.filter(is_active=True),
        'why_us':          WhyUs.objects.filter(is_active=True),
        'stats':           stats,
        'contact_form':    ContactForm(),
        # ── SEO ──
        'meta_title':       meta_title,
        'meta_description': meta_description,
        'base_url':         base_url,
        'canonical_url':    base_url + request.path,
        'alt_lang_urls':    _alt_lang_urls(request, base_url),
        'og_locale':        OG_LOCALES.get(lang, lang),
        'og_locale_alternates': [v for k, v in OG_LOCALES.items() if k != lang],
        'organization_jsonld': _organization_jsonld(site, base_url, meta_description),
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
        'Disallow: /contact/',
        '',
        f'Sitemap: {base_url}/sitemap.xml',
    ]
    return HttpResponse('\n'.join(lines), content_type='text/plain')
