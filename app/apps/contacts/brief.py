"""Вопросы брифа — единственный источник: из него строятся форма, страница
/brief/ и карточка брифа в админке.

Типы полей: text, email, tel, textarea, radio (один вариант), multi (несколько),
consent (обязательная галочка).
"""
from django.utils.translation import gettext_lazy as _


def q(key, kind, label, *, options=None, required=False, hint='', placeholder=''):
    return {'key': key, 'kind': kind, 'label': label, 'options': options or [],
            'required': required, 'hint': hint, 'placeholder': placeholder}


STEPS = [
    {
        'key': 'about',
        'title': _('О вас'),
        'intro': _('Как к вам обращаться и как удобнее связаться.'),
        'fields': [
            q('name', 'text', _('Имя'), required=True, placeholder=_('Ваше имя')),
            q('company', 'text', _('Компания'), placeholder=_('Название компании или проекта')),
            q('industry', 'text', _('Сфера бизнеса'), placeholder=_('Например: логистика, клиника, ритейл')),
            q('role', 'text', _('Ваша роль'), placeholder=_('Например: владелец, директор, менеджер')),
            q('phone', 'tel', _('Телефон / WhatsApp'), placeholder='+996 XXX XXX XXX'),
            q('email', 'email', 'Email', placeholder='name@company.com'),
            q('telegram', 'text', _('Telegram'), placeholder='@username'),
            q('contact_method', 'radio', _('Как удобнее связаться'), options=[
                ('telegram', _('Telegram')), ('whatsapp', _('WhatsApp')),
                ('call', _('Звонок')), ('email', 'Email'),
            ]),
        ],
    },
    {
        'key': 'product',
        'title': _('Продукт'),
        'intro': _('Что вы хотите создать и зачем.'),
        'fields': [
            q('product_types', 'multi', _('Что нужно'), required=True, options=[
                ('website', _('Сайт')), ('platform', _('Веб-платформа или сервис')),
                ('crm', _('CRM или внутренняя система')), ('mobile', _('Мобильное приложение')),
                ('bot', _('Telegram-бот')), ('automation', _('Автоматизация процессов')),
                ('integrations', _('Интеграции')), ('ai', _('AI-ассистент')), ('other', _('Другое')),
            ]),
            q('stage', 'radio', _('На каком этапе проект'), required=True, options=[
                ('idea', _('Есть только идея')), ('spec', _('Есть описание или ТЗ')),
                ('design', _('Есть дизайн')), ('existing', _('Продукт есть, нужна доработка или переделка')),
            ]),
            q('idea', 'textarea', _('Опишите продукт своими словами'), required=True,
              placeholder=_('Что это, для кого и как должно работать')),
            q('problem', 'textarea', _('Какую задачу бизнеса он решает'),
              placeholder=_('Что сейчас неудобно, где теряете время или деньги')),
            q('goal', 'textarea', _('Как вы поймёте, что проект удался'),
              placeholder=_('Например: больше заявок, меньше ручной работы, контроль сотрудников')),
        ],
    },
    {
        'key': 'features',
        'title': _('Пользователи и функции'),
        'intro': _('Кто будет пользоваться продуктом и что он должен уметь.'),
        'fields': [
            q('audience', 'multi', _('Кто пользователи'), options=[
                ('clients', _('Клиенты')), ('staff', _('Сотрудники')),
                ('partners', _('Партнёры или дилеры')), ('management', _('Руководство')),
            ]),
            q('users_count', 'radio', _('Сколько пользователей ожидаете'), options=[
                ('lt100', _('До 100')), ('lt1000', _('100–1 000')), ('lt10000', _('1 000–10 000')),
                ('gt10000', _('Больше 10 000')), ('unknown', _('Пока не знаю')),
            ]),
            q('features', 'textarea', _('Ключевые функции'), required=True,
              placeholder=_('Например: заявки, личный кабинет, оплата, отчёты, роли сотрудников')),
            q('mvp', 'textarea', _('Что обязательно в первой версии'),
              hint=_('Можно начать с главного и развивать продукт по этапам.')),
            q('platforms', 'multi', _('Где должен работать продукт'), options=[
                ('web', _('Сайт или веб-приложение')), ('admin', _('Веб-админка')),
                ('ios', 'iOS'), ('android', 'Android'), ('telegram', 'Telegram'),
            ]),
            q('languages', 'multi', _('Языки'), options=[
                ('ru', _('Русский')), ('ky', _('Кыргызский')), ('en', _('Английский')), ('other', _('Другой')),
            ]),
            q('integrations', 'multi', _('С чем нужно связать'), options=[
                ('payments', _('Онлайн-оплата')), ('accounting', _('1С или учётная система')),
                ('messengers', _('Telegram или WhatsApp')), ('sms', _('SMS')),
                ('crm', _('Существующая CRM')), ('maps', _('Карты или доставка')), ('other', _('Другое')),
            ]),
            q('integrations_note', 'textarea', _('Подробнее об интеграциях'),
              placeholder=_('Какие сервисы и что они должны передавать')),
        ],
    },
    {
        'key': 'design',
        'title': _('Дизайн и контент'),
        'intro': _('Как продукт должен выглядеть и что уже готово.'),
        'fields': [
            q('brand', 'radio', _('Фирменный стиль'), options=[
                ('brandbook', _('Есть брендбук')), ('logo', _('Есть только логотип')),
                ('none', _('Ничего нет, нужно сделать')),
            ]),
            q('references', 'textarea', _('Примеры, которые нравятся'),
              placeholder=_('Ссылки на сайты или приложения и что именно в них нравится')),
            q('antireferences', 'textarea', _('Что точно не нравится')),
            q('content', 'radio', _('Тексты и фото'), options=[
                ('ready', _('Готовы')), ('partial', _('Готовы частично')), ('help', _('Нужна помощь')),
            ]),
            q('current_systems', 'textarea', _('Чем пользуетесь сейчас'),
              placeholder=_('Например: Excel, Google Sheets, 1С, старый сайт')),
        ],
    },
    {
        'key': 'terms',
        'title': _('Сроки и формат'),
        'intro': _('Последний шаг — сроки, бюджет и как будем работать.'),
        'fields': [
            q('deadline', 'radio', _('Когда нужен запуск'), required=True, options=[
                ('asap', _('Срочно, до месяца')), ('1_3', _('Через 1–3 месяца')),
                ('3_6', _('Через 3–6 месяцев')), ('flexible', _('Сроки не горят')),
            ]),
            q('deadline_reason', 'text', _('Есть ли важная дата'),
              placeholder=_('Например: открытие филиала, сезон, выставка')),
            q('budget', 'radio', _('Ориентир по бюджету'), options=[
                ('lt1k', _('До $1 000')), ('1_3k', '$1 000–3 000'), ('3_7k', '$3 000–7 000'),
                ('7_15k', '$7 000–15 000'), ('gt15k', _('Больше $15 000')), ('discuss', _('Обсудим')),
            ], hint=_('Помогает сразу предложить подходящий объём работ.')),
            q('format', 'radio', _('Формат сотрудничества'), options=[
                ('partnership', _('Технологическое партнёрство')), ('revenue_share', _('Партнёрство за процент с дохода')),
                ('development', _('Разработка под заказ')), ('unknown', _('Пока не знаю')),
            ]),
            q('support', 'radio', _('Сопровождение после запуска'), options=[
                ('yes', _('Нужно')), ('no', _('Не нужно')), ('discuss', _('Обсудим')),
            ]),
            q('decision_maker', 'text', _('Кто принимает решение по проекту'),
              placeholder=_('Например: я, совет директоров, владелец')),
            q('materials', 'text', _('Ссылка на материалы'),
              placeholder=_('Google Drive, Figma, ТЗ — если есть')),
            q('extra', 'textarea', _('Что ещё важно знать')),
            q('consent', 'consent', _('Согласен на обработку данных для связи по проекту'), required=True),
        ],
    },
]

FIELDS = {f['key']: f for step in STEPS for f in step['fields']}
