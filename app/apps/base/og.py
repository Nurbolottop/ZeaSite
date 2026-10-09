"""Картинка-превью страницы партнёра для соцсетей (Open Graph, 1200×630).

Рисуется Pillow из данных CMS и кешируется в MEDIA_ROOT/og/; ключ кеша —
хеш содержимого, поэтому после правок в админке картинка обновится сама.
"""
import hashlib
import os

from django.conf import settings
from django.contrib.staticfiles import finders
from django.utils.translation import get_language, gettext as _
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
MILK, INK, MUTED = (250, 248, 244), (23, 24, 28), (90, 93, 102)
LIME, LIME_D, CORAL, CORAL_D, SKY = (212, 232, 154), (169, 191, 94), (239, 162, 142), (207, 138, 118), (195, 213, 238)
VERSION = '1'


def _font(name, size, weight='Bold'):
    font = ImageFont.truetype(finders.find(f'fonts/{name}.ttf'), size)
    try:
        font.set_variation_by_name(weight)
    except (OSError, ValueError):
        pass
    return font


def _fit(draw, text, name, size, weight, max_width, min_size=28):
    """Уменьшает кегль, пока строка не влезет в max_width."""
    while size > min_size:
        font = _font(name, size, weight)
        if draw.textlength(text, font=font) <= max_width:
            return font
        size -= 4
    return _font(name, min_size, weight)


def _logo_tile(img, path, box, radius=28):
    x0, y0, x1, y1 = box
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((x0, y0 + 7, x1, y1 + 7), radius, fill=INK)
    d.rounded_rectangle(box, radius, fill=(255, 255, 255), outline=INK, width=3)
    if path and os.path.exists(path):
        logo = Image.open(path).convert('RGBA')
        pad = int((x1 - x0) * .14)
        logo.thumbnail((x1 - x0 - 2 * pad, y1 - y0 - 2 * pad), Image.LANCZOS)
        img.paste(logo, (x0 + (x1 - x0 - logo.width) // 2, y0 + (y1 - y0 - logo.height) // 2), logo)


def _ring(d, cx, cy, r, color, dark):
    d.ellipse((cx - r - 22, cy - r - 22, cx + r + 22, cy + r + 22), fill=INK)
    d.ellipse((cx - r - 19, cy - r - 19, cx + r + 19, cy + r + 19), fill=color)
    d.ellipse((cx - r + 6, cy - r + 6, cx + r - 6, cy + r - 6), fill=dark)
    d.ellipse((cx - r + 19, cy - r + 19, cx + r - 19, cy + r - 19), fill=INK)
    d.ellipse((cx - r + 22, cy - r + 22, cx + r - 22, cy + r - 22), fill=MILK)


def partner_card(partner, stats, site_name, domain):
    """Путь к PNG-карточке партнёра (создаётся при первом запросе)."""
    lang = get_language() or 'ru'
    logo_path = partner.logo.path if partner.logo else ''
    key = '|'.join(map(str, [VERSION, lang, partner.name, partner.industry, logo_path, stats['projects'],
                             stats['since'], ','.join(stats['technologies'][:6]), site_name, domain]))
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    out_dir = os.path.join(settings.MEDIA_ROOT, 'og')
    out = os.path.join(out_dir, f'partner-{partner.slug}-{lang}-{digest}.png')
    if os.path.exists(out):
        return out
    os.makedirs(out_dir, exist_ok=True)

    img = Image.new('RGB', (W, H), MILK)
    d = ImageDraw.Draw(img)
    for x in range(30, W, 30):                      # точечная сетка
        for y in range(30, H, 30):
            d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(220, 220, 222))
    d.rounded_rectangle((24, 24, W - 24, H - 24), 40, outline=INK, width=3)

    # кольца «ZEA × партнёр» справа
    _ring(d, 905, 300, 120, LIME, LIME_D)
    _ring(d, 1045, 300, 120, CORAL, CORAL_D)

    # ZEA × логотип партнёра
    d.rounded_rectangle((80, 87, 190, 197), 26, fill=INK)
    d.rounded_rectangle((80, 80, 190, 190), 26, fill=LIME, outline=INK, width=3)
    z = _font('Unbounded', 60, 'Bold')
    d.text((135, 135), (site_name or 'ZEA')[:1], font=z, fill=INK, anchor='mm')
    d.text((232, 135), '×', font=_font('Manrope', 64, 'Bold'), fill=INK, anchor='mm')
    _logo_tile(img, logo_path, (274, 80, 384, 190), 26)

    label = _('Технологический партнёр').upper() + f' {site_name}'.upper()
    d.text((80, 248), label, font=_font('Manrope', 22, 'ExtraBold'), fill=MUTED)
    name_font = _fit(d, partner.name, 'Unbounded', 76, 'Bold', 640)
    d.text((76, 282), partner.name, font=name_font, fill=INK)

    y = 400
    if partner.industry:
        f = _font('Manrope', 26, 'Bold')
        w = d.textlength(partner.industry, font=f)
        d.rounded_rectangle((80, y, 80 + w + 44, y + 50), 25, fill=SKY, outline=INK, width=2)
        d.text((102, y + 25), partner.industry, font=f, fill=INK, anchor='lm')

    # цифры
    cells = []
    if stats['projects']:
        cells.append((str(stats['projects']), _('Проекты')))
    if stats['since']:
        cells.append((str(stats['since']), _('Вместе с')))
    if stats['technologies']:
        cells.append((str(len(stats['technologies'])), _('Технологии')))
    x = 80
    for value, caption in cells[:3]:
        d.text((x, 490), value, font=_font('Unbounded', 48, 'Bold'), fill=INK)
        d.text((x, 552), caption, font=_font('Manrope', 22, 'Bold'), fill=MUTED)
        x += 210

    d.text((W - 80, H - 72), domain, font=_font('Manrope', 24, 'Bold'), fill=INK, anchor='rm')
    img.save(out, 'PNG', optimize=True)
    return out
