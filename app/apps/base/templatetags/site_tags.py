from django import template

register = template.Library()


@register.filter
def split_accent(value, sep=' — '):
    """«ZEA — технологический партнёр» → ('ZEA —', 'технологический партнёр').
    Вторая часть выводится градиентом. Без разделителя — ('', value)."""
    value = value or ''
    if sep in value:
        head, tail = value.split(sep, 1)
        return head + sep.rstrip(), tail
    return '', value


@register.filter
def initials(value):
    """«Cleaning KIKI» → «CK»: монограмма для обложки проекта без скриншота."""
    return ''.join(word[0] for word in (value or '').split()[:2]).upper()
