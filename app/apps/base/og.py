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
VERSION = '2'


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

    # логотип ZEA Hub × логотип партнёра
    d.rounded_rectangle((80, 87, 190, 197), 26, fill=INK)
    d.rounded_rectangle((80, 80, 190, 190), 26, fill=(17, 17, 17), outline=INK, width=3)
    zea = Image.open(finders.find('img/zea-logo-white.png')).convert('RGBA')
    zea.thumbnail((86, 86), Image.LANCZOS)
    img.paste(zea, (135 - zea.width // 2, 135 - zea.height // 2), zea)
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


def _qr(url, size):
    """QR-код ссылки: графит на белом, с «тихой зоной», для печати и фото."""
    import qrcode
    from qrcode.constants import ERROR_CORRECT_M
    qr = qrcode.QRCode(error_correction=ERROR_CORRECT_M, border=2, box_size=10)
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color=INK, back_color=(255, 255, 255)).convert('RGB').resize((size, size), Image.NEAREST)


def partner_photo_card(partner, stats, site_name, domain, url):
    """Карточка-визитка партнёра 1080×1350 (для Instagram, WhatsApp, Telegram).

    QR ведёт на страницу партнёра: телефон распознаёт его прямо на фото."""
    lang = get_language() or 'ru'
    logo_path = partner.logo.path if partner.logo else ''
    key = '|'.join(map(str, ['card', VERSION, lang, partner.name, partner.industry, logo_path, stats['projects'],
                             stats['since'], len(stats['technologies']), ','.join(stats['types'][:3]),
                             site_name, domain, url]))
    digest = hashlib.sha1(key.encode()).hexdigest()[:12]
    out_dir = os.path.join(settings.MEDIA_ROOT, 'og')
    out = os.path.join(out_dir, f'card-{partner.slug}-{lang}-{digest}.png')
    if os.path.exists(out):
        return out
    os.makedirs(out_dir, exist_ok=True)

    CW, CH = 1080, 1350
    img = Image.new('RGB', (CW, CH), MILK)
    d = ImageDraw.Draw(img)
    for x in range(36, CW, 36):
        for y in range(36, CH, 36):
            d.ellipse((x - 1, y - 1, x + 1, y + 1), fill=(220, 220, 222))
    # карточка с «тенью»
    d.rounded_rectangle((60, 70, CW - 52, CH - 52), 56, fill=INK)
    d.rounded_rectangle((52, 60, CW - 60, CH - 62), 56, fill=(255, 255, 255), outline=INK, width=4)

    # кольца ZEA × партнёр (декор справа сверху)
    _ring(d, 812, 192, 62, LIME, LIME_D)
    _ring(d, 906, 192, 62, CORAL, CORAL_D)

    # логотипы
    d.rounded_rectangle((112, 128, 262, 278), 34, fill=INK)
    d.rounded_rectangle((112, 120, 262, 270), 34, fill=(17, 17, 17), outline=INK, width=4)
    zea = Image.open(finders.find('img/zea-logo-white.png')).convert('RGBA')
    zea.thumbnail((118, 118), Image.LANCZOS)
    img.paste(zea, (187 - zea.width // 2, 195 - zea.height // 2), zea)
    d.text((316, 195), '×', font=_font('Manrope', 72, 'Bold'), fill=INK, anchor='mm')
    _logo_tile(img, logo_path, (370, 120, 520, 270), 34)

    # текст
    d = ImageDraw.Draw(img)
    label = (_('Технологический партнёр') + f' {site_name}').upper()
    d.text((112, 360), label, font=_font('Manrope', 28, 'ExtraBold'), fill=MUTED)
    name_font = _fit(d, partner.name, 'Unbounded', 104, 'Bold', CW - 224, min_size=44)
    d.text((106, 400), partner.name, font=name_font, fill=INK)

    y = 560
    chips = ([partner.industry] if partner.industry else []) + stats['types'][:2]
    x = 112
    for i, text in enumerate(chips):
        f = _font('Manrope', 30, 'Bold')
        w = d.textlength(text, font=f)
        if x + w + 56 > CW - 112:
            break
        d.rounded_rectangle((x, y, x + w + 52, y + 62), 31, fill=SKY if i == 0 else (255, 255, 255), outline=INK, width=3)
        d.text((x + 26, y + 31), text, font=f, fill=INK, anchor='lm')
        x += w + 52 + 14

    # цифры
    cells = []
    if stats['projects']:
        cells.append((str(stats['projects']), _('Проекты')))
    if stats['since']:
        cells.append((str(stats['since']), _('Вместе с')))
    if stats['technologies']:
        cells.append((str(len(stats['technologies'])), _('Технологии')))
    if not cells and partner.about:
        # без проектов — описание партнёра вместо цифр
        f = _font('Manrope', 34, 'Medium')
        words, lines, line = partner.about.split(), [], ''
        for w in words:
            test = (line + ' ' + w).strip()
            if d.textlength(test, font=f) <= CW - 224:
                line = test
            else:
                lines.append(line); line = w
        lines.append(line)
        for i, ln in enumerate(lines[:4]):
            d.text((112, 700 + i * 50), ln, font=f, fill=(60, 63, 70))
    if cells:
        d.line((112, 690, CW - 112, 690), fill=(200, 201, 205), width=3)
        x = 112
        for value, caption in cells[:3]:
            d.text((x, 720), value, font=_font('Unbounded', 72, 'Bold'), fill=INK)
            d.text((x, 812), caption.upper(), font=_font('Manrope', 24, 'ExtraBold'), fill=MUTED)
            x += 290

    # QR-блок внизу
    qy, qb = 900, CH - 122
    d.rounded_rectangle((112, qy, CW - 112, qb), 40, fill=LIME, outline=INK, width=4)
    qsize = 248
    qx = CW - 112 - 40 - qsize
    qt = qy + (qb - qy - qsize) // 2
    d.rounded_rectangle((qx - 16, qt - 16, qx + qsize + 16, qt + qsize + 16), 24, fill=(255, 255, 255), outline=INK, width=3)
    img.paste(_qr(url, qsize), (qx, qt))
    tw = qx - 16 - 40 - 152
    head = _('Наведите камеру')
    d.text((152, qy + 44), head, font=_fit(d, head, 'Unbounded', 40, 'Bold', tw, min_size=26), fill=INK)
    hint = _('или нажмите на QR-код на фото')
    d.text((152, qy + 104), hint, font=_fit(d, hint, 'Manrope', 28, 'Bold', tw, min_size=18), fill=INK)
    d.text((152, qb - 112), domain, font=_fit(d, domain, 'Unbounded', 36, 'Bold', tw, min_size=22), fill=INK)
    sub = _('Проекты и история партнёрства')
    d.text((152, qb - 62), sub, font=_fit(d, sub, 'Manrope', 24, 'Bold', tw, min_size=16), fill=(60, 63, 70))
    img.save(out, 'PNG', optimize=True)
    return out
