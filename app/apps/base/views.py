import json
import os
from django.shortcuts import get_object_or_404, render
from urllib.parse import urlparse

from django.http import FileResponse, HttpResponse
from django.urls import reverse
from django.utils import translation
from django.utils.translation import gettext_lazy as _
from django.conf import settings as dj_settings
from django.contrib.staticfiles import finders
from apps.cms.models import (
    Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings,
    CooperationFormat, ProcessStep, Commitment, TeamMember,
)
from apps.contacts.forms import ContactForm


TAILWIND_PATH = os.path.join('css', 'tailwind.css')
OG_LOCALES = {'ru': 'ru_RU', 'ky': 'ky_KG', 'en': 'en_US'}

_TAILWIND_CSS = None

# Вертикальные иллюстрации занимают высокую ячейку бенто, остальные — широкую
TALL_ILLUSTRATIONS = {'mobile', 'ai', 'support'}


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


def _lang_paths(url_name='index', **kwargs):
    """Путь текущей страницы на каждом языке (переключатель языка, hreflang)."""
    paths = {}
    for code, _name in dj_settings.LANGUAGES:
        with translation.override(code):
            paths[code] = reverse(url_name, kwargs=kwargs or None)
    return paths


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


def _bento(services):
    """Раскладка «Направлений» (сетка из 6 колонок, grid-auto-flow: dense).

    Высокая карточка (2×2) идёт в паре с двумя широкими (4×1), стороны
    чередуются. Порядок из админки сохраняется внутри каждой группы.
    Оставшиеся широкие растягиваются на всю ширину. None — карточка-призыв.
    Возвращает список (service | None, layout, side)."""
    talls = [s for s in services if s.illustration_key in TALL_ILLUSTRATIONS]
    wides = [s for s in services if s.illustration_key not in TALL_ILLUSTRATIONS] + [None]
    cells, right = [], True
    while talls and len(wides) >= 2:
        tall = (talls.pop(0), 'tall', 'right' if right else 'left')
        w1, w2 = (wides.pop(0), 'wide', ''), (wides.pop(0), 'wide', '')
        # Слева высокая должна стоять в DOM первой, иначе широкая займёт её колонки
        cells += [w1, tall, w2] if right else [tall, w1, w2]
        right = not right
    cells += [(t, 'tall', 'right') for t in talls]
    cells += [(w, 'full', '') for w in wides]
    return cells


def _site_context(request, *, url_name='index', url_kwargs=None, meta_title='', meta_description=''):
    """Общий контекст публичных страниц: настройки, меню, SEO, языки."""
    site = SiteSettings.get()
    base_url = site.get_base_url(request)
    lang = translation.get_language()
    on_index = url_name == 'index'
    home = '' if on_index else reverse('index')

    has_projects = Project.objects.filter(is_active=True).exists()
    has_partners = Partner.objects.filter(is_active=True).exists()
    nav_items = [(home + '#services', _('Направления'))]
    if has_projects:
        nav_items.append((home + '#projects', _('Проекты')))
    if has_partners:
        nav_items.append((reverse('site_partners'), _('Партнёры')))
    nav_items += [(home + '#about', _('О нас')), (home + '#cooperation', _('Сотрудничество')),
                  (home + '#contact', _('Контакты'))]

    meta_title = str(meta_title or site.meta_title or f'{site.site_name} — {site.site_tagline}')
    meta_description = str(meta_description or site.meta_description or site.hero_subtitle)
    lang_paths = _lang_paths(url_name, **(url_kwargs or {}))
    return {
        'settings':        site,
        'tailwind_inline': _tailwind_inline(),
        'nav_items':       nav_items,
        'home_url':        home + '#home' if home else '#home',
        'contact_url':     home + '#contact',
        'lang_paths':      lang_paths,
        # ── SEO ──
        'meta_title':       meta_title,
        'meta_description': meta_description,
        'base_url':         base_url,
        'canonical_url':    base_url + request.path,
        'alt_lang_urls':    {code: base_url + path for code, path in lang_paths.items()},
        'og_locale':        OG_LOCALES.get(lang, lang),
        'og_locale_alternates': [v for k, v in OG_LOCALES.items() if k != lang],
        'organization_jsonld': _organization_jsonld(site, base_url, meta_description),
    }


def _active_projects():
    return list(Project.objects.filter(is_active=True).order_by('-is_featured', 'order')
                .prefetch_related('gallery'))


def index(request):
    projects = _active_projects()
    context = _site_context(request)
    context.update({
        'commitments':     Commitment.objects.filter(is_active=True),
        'formats':         CooperationFormat.objects.filter(is_active=True),
        'process_steps':   ProcessStep.objects.filter(is_active=True),
        'bento':           _bento(list(Service.objects.filter(is_active=True))),
        'team':            TeamMember.objects.filter(is_active=True),
        'projects':        projects,
        'hero_projects':   [p for p in projects if p.is_featured][:2],
        'partners':        list(Partner.objects.filter(is_active=True)),
        'tech_stack':      TechStack.objects.filter(is_active=True),
        'why_us':          WhyUs.objects.filter(is_active=True),
        'stats':           list(Stat.objects.filter(is_active=True)),
        'contact_form':    ContactForm(),
    })
    return render(request, 'index.html', context)


def partners(request):
    items = list(Partner.objects.filter(is_active=True).prefetch_related('projects'))
    context = _site_context(request, url_name='site_partners',
                            meta_title=f"{_('Партнёры')} — {SiteSettings.get().site_name}",
                            meta_description=_('Компании и организации, с которыми работает ZEA.'))
    context['partners'] = items
    return render(request, 'site/partners_list.html', context)


def partner_detail(request, slug):
    partner = get_object_or_404(Partner, slug=slug, is_active=True)
    projects = list(partner.projects.filter(is_active=True).order_by('-is_featured', 'order')
                    .prefetch_related('gallery'))
    context = _site_context(request, url_name='site_partner', url_kwargs={'slug': slug},
                            meta_title=f'{partner.name} — {_("партнёр")} {SiteSettings.get().site_name}',
                            meta_description=partner.about or partner.industry)
    context.update({
        'partner':  partner,
        'projects': projects,
        'stats':    partner.card_stats(projects),
        'og_image_url': context['base_url'] + reverse('site_partner_og', kwargs={'slug': slug}),
        'others':   list(Partner.objects.filter(is_active=True).exclude(pk=partner.pk)),
    })
    return render(request, 'site/partner_detail.html', context)


def partner_og(request, slug):
    """PNG-превью страницы партнёра для Telegram, WhatsApp, соцсетей."""
    from .og import partner_card
    partner = get_object_or_404(Partner, slug=slug, is_active=True)
    projects = list(partner.projects.filter(is_active=True))
    site = SiteSettings.get()
    domain = urlparse(site.get_base_url(request)).netloc
    path = partner_card(partner, partner.card_stats(projects), site.site_name, domain)
    response = FileResponse(open(path, 'rb'), content_type='image/png')
    response['Cache-Control'] = 'public, max-age=86400'
    return response


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
