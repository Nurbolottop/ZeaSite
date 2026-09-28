"""Утверждённый контент публичного сайта (RU — основной, KY/EN — переводы).

Используется:
  * миграцией cms/0010 — один раз заполняет ПУСТЫЕ блоки на новой структуре;
  * командой `manage.py populate_db` — безопасное повторное заполнение.

Правила безопасности (не нарушать):
  * ничего не удаляется;
  * тексты SiteSettings заменяются, только если поле пустое или содержит
    старое значение по умолчанию (то есть его никто не редактировал);
  * проекты, партнёры и статистика здесь НЕ создаются — только реальные
    данные, вручную через админку.

Функции принимают словарь моделей, поэтому работают и с историческими
моделями внутри миграции, и с обычными моделями в команде.
"""

LANGS = ('ru', 'ky', 'en')
SITE_DOMAIN = 'https://zeastudio.su'


def t(ru, ky, en):
    return {'ru': ru, 'ky': ky, 'en': en}


# ── SiteSettings ────────────────────────────────────────────────────────────
TAGLINE = t('Технологический партнёр для бизнеса',
            'Бизнес үчүн технологиялык өнөктөш',
            'Technology partner for business')

SITE_SETTINGS = {
    'site_tagline': TAGLINE,
    'hero_badge': TAGLINE,
    'hero_title': t('ZEA — технологический партнёр для бизнеса',
                    'ZEA — бизнес үчүн технологиялык өнөктөш',
                    'ZEA — a technology partner for business'),
    'hero_subtitle': t(
        'Проектируем, разрабатываем, запускаем и сопровождаем цифровые продукты. '
        'Работаем как ваша IT-команда: долгосрочно или под конкретную задачу.',
        'Санариптик продукттарды долбоорлойбуз, иштеп чыгабыз, ишке киргизебиз жана колдоп турабыз. '
        'Сиздин IT-командаңыз катары иштейбиз: узак мөөнөткө же конкреттүү тапшырма боюнча.',
        'We design, build, launch and support digital products. '
        'We work as your IT team — long-term or for a specific project.'),
    'about_text': t(
        'ZEA создаёт цифровые продукты и системы для бизнеса — от сайтов и внутренних платформ '
        'до CRM, мобильных приложений и автоматизации. Мы не заканчиваем работу после запуска: '
        'сопровождаем продукт, развиваем его и адаптируем под новые задачи компании.',
        'ZEA бизнес үчүн санариптик продукттарды жана системаларды түзөт — сайттардан жана ички '
        'платформалардан баштап CRM, мобилдик тиркемелерге жана автоматташтырууга чейин. Ишке '
        'киргизгенден кийин да ишибизди токтотпойбуз: продуктту колдоп, өнүктүрүп, компаниянын '
        'жаңы милдеттерине ылайыкташтырабыз.',
        'ZEA builds digital products and systems for business — from websites and internal '
        'platforms to CRM, mobile apps and automation. Our work does not end at launch: we support '
        'the product, keep developing it and adapt it to the company\'s new needs.'),
    'meta_title': t(
        'ZEA — технологический партнёр для бизнеса · Разработка и сопровождение',
        'ZEA — бизнес үчүн технологиялык өнөктөш · Иштеп чыгуу жана колдоо',
        'ZEA — Technology Partner for Business · Development and Support'),
    'meta_description': t(
        'ZEA берёт на себя технологическую часть бизнеса: анализ, разработку сайтов, CRM, '
        'веб-систем и приложений, автоматизацию, запуск и сопровождение.',
        'ZEA бизнестин технологиялык бөлүгүн өзүнө алат: талдоо, сайттарды, CRM, веб-системаларды '
        'жана тиркемелерди иштеп чыгуу, автоматташтыруу, ишке киргизүү жана колдоо.',
        'ZEA takes care of the technology side of your business: analysis, development of websites, '
        'CRM, web systems and apps, automation, launch and support.'),
}

# Старые значения (дефолты модели и load_zea.py). Поле с таким значением
# считается «не отредактированным» и безопасно обновляется.
LEGACY_VALUES = {
    'site_tagline': {'IT Studio', 'IT-студия'},
    'hero_badge': {'Открыты для новых проектов', 'Жаңы долбоорлорго ачыкбыз', 'Open for new projects'},
    'hero_title': {
        'ZEA — разработка цифровых решений для бизнеса',
        'Разрабатываем цифровые решения для бизнеса',
        'Бизнес үчүн санариптик чечимдерди иштеп чыгабыз',
        'We build digital solutions for business',
    },
    'hero_subtitle': {
        'Создаём сайты, CRM-системы, Telegram-ботов и внутренние платформы для автоматизации '
        'бизнес-процессов.',
        'Создаём сайты, CRM-системы, Telegram-ботов и backend на Django, PostgreSQL и Docker. '
        'Помогаем бизнесу автоматизировать процессы и запускать рабочие продукты.',
        'Сайттарды, CRM-системаларды, Telegram-botторду жана Django, PostgreSQL, Docker негизиндеги '
        'backend чечимдерди түзөбүз. Бизнеске процесстерди автоматташтырууга жана иштеген '
        'продукттарды чыгарууга жардам беребиз.',
        'We create websites, CRM systems, Telegram bots and backend solutions with Django, '
        'PostgreSQL and Docker. We help businesses automate workflows and launch working products.',
    },
    'about_text': {
        'ZEA — мини IT-студия, которая помогает бизнесам запускать современные цифровые продукты. '
        'Мы разрабатываем сайты, CRM-системы, Telegram-ботов и решения для автоматизации процессов.',
        'ZEA — IT-студия из Бишкека. Делаем понятные и надёжные цифровые продукты для бизнеса: '
        'от идеи и структуры до backend, дизайна, деплоя и поддержки после запуска.',
        'ZEA — Бишкектеги IT-студия. Бизнес үчүн түшүнүктүү жана ишеничтүү санариптик продукттарды '
        'жасайбыз: идеядан жана структурадан баштап backend, дизайн, деплой жана иштеп чыккандан '
        'кийинки колдоого чейин.',
        'ZEA is an IT studio based in Bishkek. We build clear and reliable digital products for '
        'business — from idea and structure to backend, design, deployment and post-launch support.',
    },
    'meta_title': {
        'ZEA IT Studio — сайты, CRM, Telegram-боты и backend-разработка',
        'ZEA IT Studio — сайттар, CRM, Telegram-боттор жана backend иштеп чыгуу',
        'ZEA IT Studio — Websites, CRM, Telegram Bots & Backend Development',
    },
    'meta_description': {
        'ZEA — IT-студия из Бишкека. Разрабатываем сайты, CRM-системы, Telegram-ботов, backend на '
        'Django/PostgreSQL/Docker и UI/UX-дизайн для бизнеса.',
        'ZEA — Бишкектеги IT-студия. Бизнес үчүн сайттарды, CRM-системаларды, Telegram-botторду, '
        'Django/PostgreSQL/Docker backend жана UI/UX дизайнды иштеп чыгабыз.',
        'ZEA is an IT studio from Bishkek. We develop websites, CRM systems, Telegram bots, '
        'Django/PostgreSQL/Docker backend and UI/UX design for business.',
    },
}

# Устаревший текст подвала очищается: шаблон сам выводит «© <год> ZEA».
LEGACY_FOOTERS = {
    '© 2024 ZEA IT Studio. All rights reserved.',
    '© 2026 ZEA IT Studio. Цифровые решения для бизнеса.',
    '© 2026 ZEA IT Studio. Бизнес үчүн санариптик чечимдер.',
    '© 2026 ZEA IT Studio. Digital solutions for business.',
}

# Заглушки из старых дефолтов модели — это не реальные контакты ZEA.
PLACEHOLDER_CONTACTS = {
    'telegram_url': 'https://t.me/zea_studio',
    'whatsapp_url': 'https://wa.me/996700000000',
    'instagram_url': 'https://instagram.com/zea.studio',
    'email': 'hello@zea.dev',
}


# ── Что мы берём на себя ────────────────────────────────────────────────────
COMMITMENTS = [
    dict(icon='search-check', color='indigo',
         title=t('Анализ', 'Талдоо', 'Analysis'),
         description=t(
             'Разбираемся в процессах бизнеса и определяем, какие задачи стоит автоматизировать '
             'в первую очередь.',
             'Бизнестин процесстерин иликтеп, алгач кайсы милдеттерди автоматташтыруу керек '
             'экенин аныктайбыз.',
             'We study your business processes and identify which tasks should be automated first.')),
    dict(icon='pencil-ruler', color='purple',
         title=t('Проектирование', 'Долбоорлоо', 'Design'),
         description=t(
             'Продумываем структуру продукта, роли пользователей, сценарии работы и интерфейсы.',
             'Продуктун түзүмүн, колдонуучулардын ролдорун, иш сценарийлерин жана интерфейстерди '
             'ойлонуштурабыз.',
             'We plan the product structure, user roles, workflows and interfaces.')),
    dict(icon='code-2', color='cyan',
         title=t('Разработка', 'Иштеп чыгуу', 'Development'),
         description=t(
             'Создаём сайты, веб-системы, CRM, мобильные приложения и интеграции.',
             'Сайттарды, веб-системаларды, CRM, мобилдик тиркемелерди жана интеграцияларды түзөбүз.',
             'We build websites, web systems, CRM, mobile apps and integrations.')),
    dict(icon='rocket', color='blue',
         title=t('Запуск', 'Ишке киргизүү', 'Launch'),
         description=t(
             'Готовим продукт к работе: сервер, домен, развёртывание и необходимые настройки.',
             'Продуктту ишке даярдайбыз: сервер, домен, жайгаштыруу жана керектүү жөндөөлөр.',
             'We get the product ready to go live: server, domain, deployment and configuration.')),
    dict(icon='life-buoy', color='green',
         title=t('Сопровождение', 'Колдоо', 'Support'),
         description=t(
             'Следим за стабильной работой, исправляем проблемы и обновляем продукт.',
             'Туруктуу иштешин көзөмөлдөп, көйгөйлөрдү оңдоп, продуктту жаңылап турабыз.',
             'We keep the product running reliably, fix issues and roll out updates.')),
    dict(icon='trending-up', color='orange',
         title=t('Развитие', 'Өнүктүрүү', 'Growth'),
         description=t(
             'Добавляем новые возможности по мере роста бизнеса и появления новых задач.',
             'Бизнес өскөн сайын жана жаңы милдеттер пайда болгон сайын жаңы мүмкүнчүлүктөрдү '
             'кошобуз.',
             'We add new capabilities as your business grows and new needs arise.')),
]


# ── Форматы сотрудничества ──────────────────────────────────────────────────
COOPERATION_FORMATS = [
    dict(icon='handshake', request_type='partnership', is_primary=True,
         title=t('Технологическое партнёрство', 'Технологиялык өнөктөштүк', 'Technology partnership'),
         audience=t(
             'Для компаний, которым нужна постоянная IT-команда, а не разовый подрядчик.',
             'Бир жолку аткаруучу эмес, туруктуу IT-команда керек болгон компаниялар үчүн.',
             'For companies that need a permanent IT team rather than a one-off contractor.'),
         description=t(
             'ZEA анализирует задачи бизнеса, проектирует и создаёт необходимые цифровые решения, '
             'запускает их и продолжает развивать после запуска.',
             'ZEA бизнестин милдеттерин талдап, керектүү санариптик чечимдерди долбоорлоп түзөт, '
             'ишке киргизет жана андан кийин да өнүктүрүүнү улантат.',
             'ZEA analyses your business needs, designs and builds the digital solutions you need, '
             'launches them and keeps developing them after launch.'),
         terms=t(
             'Условия сотрудничества определяются индивидуально после анализа и фиксируются договором.',
             'Кызматташтыктын шарттары талдоодон кийин жеке аныкталып, келишим менен бекитилет.',
             'Terms are agreed individually after the analysis and set out in a contract.'),
         cta_label=t('Обсудить партнёрство', 'Өнөктөштүктү талкуулоо', 'Discuss a partnership')),
    dict(icon='code-2', request_type='development', is_primary=False,
         title=t('Разработка под заказ', 'Буйрутма боюнча иштеп чыгуу', 'Custom development'),
         audience=t(
             'Для компаний, которым нужен конкретный цифровой продукт или решение.',
             'Белгилүү бир санариптик продукт же чечим керек болгон компаниялар үчүн.',
             'For companies that need a specific digital product or solution.'),
         description=t(
             'Определяем задачу, объём работ, стоимость и сроки. Разрабатываем продукт, тестируем '
             'и запускаем.',
             'Милдетти, иштин көлөмүн, баасын жана мөөнөтүн аныктайбыз. Продуктту иштеп чыгып, '
             'тестирлеп, ишке киргизебиз.',
             'We define the task, scope, cost and timeline. Then we build, test and launch the product.'),
         terms=t('', '', ''),
         cta_label=t('Заказать разработку', 'Иштеп чыгууга буйрутма берүү', 'Order development')),
]


# ── Как мы начинаем работу ──────────────────────────────────────────────────
PROCESS_STEPS = [
    dict(title=t('Заявка', 'Өтүнмө', 'Request'),
         description=t('Вы рассказываете о бизнесе и задаче.',
                       'Бизнесиңиз жана милдетиңиз тууралуу айтып бересиз.',
                       'You tell us about your business and the task.')),
    dict(title=t('Анализ', 'Талдоо', 'Analysis'),
         description=t('Изучаем процессы, потребности и текущие инструменты.',
                       'Процесстерди, муктаждыктарды жана учурдагы куралдарды иликтейбиз.',
                       'We study your processes, needs and current tools.')),
    dict(title=t('Решение', 'Чечим', 'Solution'),
         description=t('Предлагаем, что нужно разработать или автоматизировать.',
                       'Эмнени иштеп чыгуу же автоматташтыруу керек экенин сунуштайбыз.',
                       'We propose what should be built or automated.')),
    dict(title=t('Условия и договор', 'Шарттар жана келишим', 'Terms and contract'),
         description=t('Определяем формат сотрудничества, объём работ и ответственность сторон.',
                       'Кызматташтыктын форматын, иштин көлөмүн жана тараптардын жоопкерчилигин '
                       'аныктайбыз.',
                       'We agree on the cooperation format, scope of work and responsibilities.')),
    dict(title=t('Разработка и запуск', 'Иштеп чыгуу жана ишке киргизүү', 'Development and launch'),
         description=t('Работаем по этапам и показываем промежуточный результат.',
                       'Этап-этабы менен иштеп, аралык жыйынтыкты көрсөтүп турабыз.',
                       'We work in stages and show you interim results.')),
    dict(title=t('Сопровождение', 'Колдоо', 'Support'),
         description=t('Поддерживаем и развиваем продукт после запуска.',
                       'Ишке киргизгенден кийин продуктту колдоп, өнүктүрөбүз.',
                       'We support and develop the product after launch.')),
]


# ── Направления (Service) ───────────────────────────────────────────────────
SERVICES = [
    dict(icon='globe', color='indigo',
         title=t('Сайты', 'Сайттар', 'Websites'),
         description=t('Корпоративные сайты, сервисы и решения для привлечения клиентов.',
                       'Корпоративдик сайттар, сервистер жана кардарларды тартуу үчүн чечимдер.',
                       'Corporate websites, online services and solutions that bring in customers.')),
    dict(icon='app-window', color='purple',
         title=t('Веб-системы и платформы', 'Веб-системалар жана платформалар', 'Web systems and platforms'),
         description=t('Системы для управления внутренними процессами бизнеса.',
                       'Бизнестин ички процесстерин башкаруу үчүн системалар.',
                       'Systems for managing your internal business processes.')),
    dict(icon='database', color='cyan',
         title=t('CRM и внутренние системы', 'CRM жана ички системалар', 'CRM and internal systems'),
         description=t('Клиенты, заявки, заказы, сотрудники и отчётность в одной системе.',
                       'Кардарлар, өтүнмөлөр, буйрутмалар, кызматкерлер жана отчеттуулук бир системада.',
                       'Customers, requests, orders, staff and reporting in one system.')),
    dict(icon='smartphone', color='blue',
         title=t('Мобильные приложения', 'Мобилдик тиркемелер', 'Mobile apps'),
         description=t('Продукты и сервисы для iOS и Android.',
                       'iOS жана Android үчүн продукттар жана сервистер.',
                       'Products and services for iOS and Android.')),
    dict(icon='workflow', color='green',
         title=t('Автоматизация', 'Автоматташтыруу', 'Automation'),
         description=t('Автоматизация повторяющихся процессов, заявок, уведомлений и документов.',
                       'Кайталануучу процесстерди, өтүнмөлөрдү, билдирмелерди жана документтерди '
                       'автоматташтыруу.',
                       'Automating repetitive processes, requests, notifications and documents.')),
    dict(icon='plug', color='orange',
         title=t('Интеграции', 'Интеграциялар', 'Integrations'),
         description=t('Связываем сайт, CRM, оплату, внешние сервисы и другие системы.',
                       'Сайтты, CRM, төлөмдү, тышкы сервистерди жана башка системаларды бириктиребиз.',
                       'We connect your website, CRM, payments, external services and other systems.')),
    dict(icon='life-buoy', color='pink',
         title=t('Сопровождение', 'Колдоо', 'Support'),
         description=t('Поддерживаем и развиваем уже работающие цифровые продукты.',
                       'Иштеп жаткан санариптик продукттарды колдоп, өнүктүрөбүз.',
                       'We support and develop digital products that are already live.')),
]


# ── Почему ZEA (WhyUs) ──────────────────────────────────────────────────────
WHY_US = [
    dict(icon='target', color='indigo',
         title=t('Начинаем с бизнеса, а не с технологии',
                 'Технологиядан эмес, бизнестен баштайбыз',
                 'We start with the business, not the technology'),
         description=t('Сначала разбираемся в процессах и задачах.',
                       'Адегенде процесстерди жана милдеттерди түшүнүп алабыз.',
                       'First we get to grips with your processes and goals.')),
    dict(icon='users', color='purple',
         title=t('Одна команда на весь цикл', 'Бүт цикл үчүн бир команда', 'One team for the full cycle'),
         description=t('Анализ, проектирование, разработка, запуск и сопровождение.',
                       'Талдоо, долбоорлоо, иштеп чыгуу, ишке киргизүү жана колдоо.',
                       'Analysis, design, development, launch and support.')),
    dict(icon='git-branch', color='cyan',
         title=t('Работаем по этапам', 'Этап-этабы менен иштейбиз', 'We work in stages'),
         description=t('Показываем промежуточный результат и движение проекта.',
                       'Аралык жыйынтыкты жана долбоордун жүрүшүн көрсөтүп турабыз.',
                       'You see interim results and how the project is progressing.')),
    dict(icon='shield-check', color='green',
         title=t('Остаёмся после запуска', 'Ишке киргизгенден кийин да жаныңыздабыз', 'We stay after launch'),
         description=t('Поддерживаем продукт и продолжаем его развивать.',
                       'Продуктту колдоп, өнүктүрүүнү улантабыз.',
                       'We support the product and keep developing it.')),
    dict(icon='file-text', color='orange',
         title=t('Прозрачные условия', 'Ачык шарттар', 'Clear terms'),
         description=t('Формат работы, обязанности и условия фиксируются заранее.',
                       'Иштин форматы, милдеттер жана шарттар алдын ала бекитилет.',
                       'The working format, responsibilities and terms are agreed in advance.')),
]


# ── Логика заполнения ───────────────────────────────────────────────────────
TRANSLATED = {
    'Commitment': ('title', 'description'),
    'CooperationFormat': ('title', 'audience', 'description', 'terms', 'cta_label'),
    'ProcessStep': ('title', 'description'),
    'Service': ('title', 'description'),
    'WhyUs': ('title', 'description'),
}

LIST_BLOCKS = (
    ('Commitment', COMMITMENTS),
    ('CooperationFormat', COOPERATION_FORMATS),
    ('ProcessStep', PROCESS_STEPS),
    ('Service', SERVICES),
    ('WhyUs', WHY_US),
)


def _set_ml(obj, field, value):
    """Мультиязычное поле: базовая колонка + _ru/_ky/_en."""
    setattr(obj, field, value['ru'])
    for lang in LANGS:
        setattr(obj, f'{field}_{lang}', value[lang])


def _is_default(value, field):
    return not value or value in LEGACY_VALUES.get(field, ())


def seed_site_settings(SiteSettings, force=False, log=None):
    """Обновляет только пустые или старые дефолтные значения (force — все)."""
    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    changed = []
    for field, value in SITE_SETTINGS.items():
        for lang in LANGS:
            col = f'{field}_{lang}'
            current = getattr(obj, col)
            # Русский текст в KY/EN-колонке = перевода нет (modeltranslation
            # копирует дефолт модели во все языки).
            untranslated = lang != 'ru' and current == value['ru']
            if force or untranslated or _is_default(current, field):
                setattr(obj, col, value[lang])
                changed.append(col)
        if force or _is_default(getattr(obj, field), field):
            setattr(obj, field, value['ru'])
    for col in ['footer_text'] + [f'footer_text_{lang}' for lang in LANGS]:
        if getattr(obj, col) in LEGACY_FOOTERS:
            setattr(obj, col, '')
            changed.append(col)
    for field, placeholder in PLACEHOLDER_CONTACTS.items():
        if getattr(obj, field) == placeholder:
            setattr(obj, field, '')
            changed.append(field)
    if not obj.site_domain:
        obj.site_domain = SITE_DOMAIN
        changed.append('site_domain')
    obj.save()
    if log:
        log(f'SiteSettings: обновлено полей — {len(changed)}')
    return changed


def seed_list_blocks(models, mode='missing', log=None):
    """Заполняет блоки-списки.

    mode:
      'if_empty' — только если в таблице нет ни одной записи (миграция);
      'missing'  — создать недостающие записи (поиск по русскому названию),
                   существующие не трогать;
      'update'   — как 'missing', но существующие записи перезаписать текстами.
    Удаления нет ни в одном режиме.
    """
    for name, items in LIST_BLOCKS:
        Model = models[name]
        if mode == 'if_empty' and Model.objects.exists():
            if log:
                log(f'{name}: есть записи — пропущено')
            continue
        created = updated = 0
        for order, item in enumerate(items, start=1):
            obj = Model.objects.filter(title_ru=item['title']['ru']).first()
            if obj is not None and mode != 'update':
                continue
            is_new = obj is None
            if is_new:
                obj = Model(order=order, is_active=True)
            for key, value in item.items():
                if key in TRANSLATED[name]:
                    _set_ml(obj, key, value)
                else:
                    setattr(obj, key, value)
            obj.save()
            created += is_new
            updated += not is_new
        if log:
            log(f'{name}: создано {created}, обновлено {updated}')
