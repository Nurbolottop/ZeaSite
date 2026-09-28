# -*- coding: utf-8 -*-
"""Загрузчик ЧЕРНОВИКОВ портфолио ZEA (ru/ky/en): проекты, партнёры, стек.

    docker exec -i <web> python manage.py shell < load_zea.py

БЕЗОПАСНОСТЬ:
  * ничего не удаляет (раньше скрипт начинал с Model.objects.all().delete());
  * повторный запуск обновляет записи по русскому названию (update_or_create);
  * НОВЫЕ проекты и партнёры создаются СКРЫТЫМИ (is_active=False) — данные
    не подтверждены. Показывать их на сайте — только вручную в админке
    после проверки фактов и согласия клиента;
  * у существующих записей флаг is_active не меняется (решение из админки
    сохраняется);
  * тексты сайта (hero, «О нас», услуги, «Почему ZEA») и статистика здесь
    больше НЕ загружаются: утверждённый контент — `manage.py populate_db`,
    цифры — только подтверждённые, вручную.

Не запускать на production без отдельного решения.
"""
from apps.cms.models import Project, Partner, TechStack

LANGS = ['ru', 'ky', 'en']


def setml(obj, field, val):
    """Устанавливает мультиязычное поле (base + _ru/_ky/_en)."""
    setattr(obj, field, val['ru'])
    for l in LANGS:
        setattr(obj, '%s_%s' % (field, l), val[l])


def upsert(Model, key_field, data, ml_fields, new_is_active):
    """update_or_create по русскому значению key_field; без удаления."""
    obj = Model.objects.filter(**{'%s_ru' % key_field: data[key_field]['ru']}).first()
    created = obj is None
    if created:
        obj = Model(is_active=new_is_active)
    for k, v in data.items():
        if k in ml_fields:
            setml(obj, k, v)
        else:
            setattr(obj, k, v)
    obj.save()
    return created

# PROJECTS
# ─────────────────────────────────────────────────────────────
def P(name, desc, ptype, tech, icon, color, year, order, live=''):
    return dict(name=name, description=desc, project_type=ptype, technologies=tech,
                icon=icon, color=color, year=year, order=order, live_url=live)


PROJECTS = [
    P({'ru': 'Cleaning KIKI', 'ky': 'Cleaning KIKI', 'en': 'Cleaning KIKI'},
      {'ru': 'Сайт и CRM-система для клининговой компании: заявки, клиенты, сотрудники, роли, заказы, '
             'контроль работы и аналитика.',
       'ky': 'Клининг компаниясы үчүн сайт жана CRM: өтүнмөлөр, кардарлар, кызматкерлер, ролдор, '
             'буйрутмалар, иштин көзөмөлү жана аналитика.',
       'en': 'Website and CRM system for a cleaning company: requests, clients, staff, roles, orders, '
             'work control and analytics.'},
      {'ru': 'CRM + сайт', 'ky': 'CRM + сайт', 'en': 'CRM + Website'},
      {'ru': 'Django, PostgreSQL, Docker, Redis, Nginx, JavaScript',
       'ky': 'Django, PostgreSQL, Docker, Redis, Nginx, JavaScript',
       'en': 'Django, PostgreSQL, Docker, Redis, Nginx, JavaScript'},
      'sparkles', 'indigo', 2025, 1, 'https://cleaningkiki.kg'),
    P({'ru': 'GreenEnergy', 'ky': 'GreenEnergy', 'en': 'GreenEnergy'},
      {'ru': 'IoT-платформа для мониторинга электроэнергии и управления устройствами: показатели, '
             'статусы, команды и серверная API-часть.',
       'ky': 'Электр энергиясын мониторинг кылуу жана түзмөктөрдү башкаруу үчүн IoT-платформа: '
             'көрсөткүчтөр, статустар, командалар жана серверлик API.',
       'en': 'IoT platform for energy monitoring and device control: metrics, statuses, commands and a '
             'backend API.'},
      {'ru': 'IoT-платформа', 'ky': 'IoT-платформа', 'en': 'IoT Platform'},
      {'ru': 'Django, REST API, PostgreSQL, Docker, ESP32, Linux',
       'ky': 'Django, REST API, PostgreSQL, Docker, ESP32, Linux',
       'en': 'Django, REST API, PostgreSQL, Docker, ESP32, Linux'},
      'zap', 'green', 2026, 2, 'https://greenenergy.su'),
    P({'ru': 'KIKI Academy', 'ky': 'KIKI Academy', 'en': 'KIKI Academy'},
      {'ru': 'Платформа корпоративного обучения с ролями, уроками, тестами и внутренней базой знаний '
             'для сотрудников.',
       'ky': 'Кызматкерлер үчүн ролдор, сабактар, тесттер жана ички билим базасы бар корпоративдик окуу '
             'платформасы.',
       'en': 'Corporate learning platform with roles, lessons, tests and an internal knowledge base for '
             'employees.'},
      {'ru': 'Платформа обучения', 'ky': 'Окуу платформасы', 'en': 'Learning Platform'},
      {'ru': 'Django, PostgreSQL, Docker, JavaScript, HTML, CSS',
       'ky': 'Django, PostgreSQL, Docker, JavaScript, HTML, CSS',
       'en': 'Django, PostgreSQL, Docker, JavaScript, HTML, CSS'},
      'layers', 'purple', 2026, 3),
    P({'ru': 'Терминал самооплаты', 'ky': 'Өз алдынча төлөм терминалы',
       'en': 'Self-Service Payment Terminal'},
      {'ru': 'Система для терминала самооплаты: роли, касса, QR-оплата, отчёты, настройки и контроль '
             'оборудования.',
       'ky': 'Өз алдынча төлөм терминалы үчүн система: ролдор, касса, QR-төлөм, отчёттор, жөндөөлөр жана '
             'жабдууну көзөмөлдөө.',
       'en': 'Self-service payment terminal system: roles, cashier flow, QR payments, reports, settings '
             'and hardware control.'},
      {'ru': 'Киоск-система', 'ky': 'Киоск-система', 'en': 'Kiosk System'},
      {'ru': 'Django, PostgreSQL, Docker, JavaScript, Chart.js, Linux',
       'ky': 'Django, PostgreSQL, Docker, JavaScript, Chart.js, Linux',
       'en': 'Django, PostgreSQL, Docker, JavaScript, Chart.js, Linux'},
      'smartphone', 'cyan', 2026, 4),
    P({'ru': 'AliaTex', 'ky': 'AliaTex', 'en': 'AliaTex'},
      {'ru': 'Корпоративный сайт швейного производства с презентацией компании, услуг, направлений '
             'работы и каталога.',
       'ky': 'Тигүү өндүрүшү үчүн компанияны, кызматтарды, иш багыттарын жана каталогду тааныштырган '
             'корпоративдик сайт.',
       'en': 'Corporate website for a garment manufacturer with company presentation, services, work '
             'areas and catalog.'},
      {'ru': 'Корпоративный сайт', 'ky': 'Корпоративдик сайт', 'en': 'Corporate Website'},
      {'ru': 'Django, PostgreSQL, JavaScript, Nginx', 'ky': 'Django, PostgreSQL, JavaScript, Nginx',
       'en': 'Django, PostgreSQL, JavaScript, Nginx'},
      'globe', 'blue', 2025, 5, 'https://aliyatex.kg'),
    P({'ru': 'FinicApp', 'ky': 'FinicApp', 'en': 'FinicApp'},
      {'ru': 'Финансовая backend-платформа и API-инфраструктура для управления данными и внутренними '
             'процессами.',
       'ky': 'Маалыматтарды жана ички процесстерди башкаруу үчүн финансылык backend-платформа жана '
             'API-инфраструктура.',
       'en': 'Financial backend platform and API infrastructure for managing data and internal '
             'processes.'},
      {'ru': 'Финтех-платформа', 'ky': 'Финтех-платформа', 'en': 'Financial Backend Platform'},
      {'ru': 'Django, PostgreSQL, REST API, Docker', 'ky': 'Django, PostgreSQL, REST API, Docker',
       'en': 'Django, PostgreSQL, REST API, Docker'},
      'database', 'indigo', 2026, 6),
    P({'ru': 'RusCargo', 'ky': 'RusCargo', 'en': 'RusCargo'},
      {'ru': 'Логистическая платформа для управления грузоперевозками, заказами и внутренними '
             'операциями.',
       'ky': 'Жүк ташууну, буйрутмаларды жана ички операцияларды башкаруу үчүн логистика платформасы.',
       'en': 'Logistics platform for managing freight, orders and internal operations.'},
      {'ru': 'Платформа логистики', 'ky': 'Логистика платформасы', 'en': 'Logistics Platform'},
      {'ru': 'Django, PostgreSQL, Docker', 'ky': 'Django, PostgreSQL, Docker',
       'en': 'Django, PostgreSQL, Docker'},
      'truck', 'orange', 2025, 7),
    P({'ru': 'T1Cargo', 'ky': 'T1Cargo', 'en': 'T1Cargo'},
      {'ru': 'Система управления логистикой и cargo-операциями для внутренних бизнес-процессов.',
       'ky': 'Ички бизнес-процесстер үчүн логистиканы жана жүк операцияларын башкаруу системасы.',
       'en': 'Logistics and cargo operations management system for internal business processes.'},
      {'ru': 'Система управления грузами', 'ky': 'Жүк башкаруу системасы', 'en': 'Cargo Management System'},
      {'ru': 'Django, PostgreSQL, Docker', 'ky': 'Django, PostgreSQL, Docker',
       'en': 'Django, PostgreSQL, Docker'},
      'truck', 'red', 2025, 8),
    P({'ru': 'AYOHub', 'ky': 'AYOHub', 'en': 'AYOHub'},
      {'ru': 'Платформа для организаций и пользователей с настройкой скидок и системой транзакций.',
       'ky': 'Жеңилдиктерди жөндөө жана транзакциялар системасы бар уюмдар менен колдонуучулар үчүн '
             'платформа.',
       'en': 'Platform for organizations and users with discount configuration and a transaction '
             'system.'},
      {'ru': 'Платформа скидок и транзакций', 'ky': 'Жеңилдиктер жана транзакциялар платформасы',
       'en': 'Discount & Transaction Platform'},
      {'ru': 'Django, PostgreSQL, REST API', 'ky': 'Django, PostgreSQL, REST API',
       'en': 'Django, PostgreSQL, REST API'},
      'credit-card', 'pink', 2026, 9),
    P({'ru': 'MediKana', 'ky': 'MediKana', 'en': 'MediKana'},
      {'ru': 'Платформа и интерфейс для медицинской лаборатории с каталогом анализов и динамическим '
             'отображением.',
       'ky': 'Анализдердин каталогу жана динамикалык көрсөтүүсү бар медициналык лаборатория үчүн '
             'платформа жана интерфейс.',
       'en': 'Platform and UI for a medical laboratory with a catalog of tests and dynamic rendering.'},
      {'ru': 'Медицинская платформа', 'ky': 'Медициналык платформа', 'en': 'Healthcare Platform'},
      {'ru': 'HTML, CSS, JavaScript', 'ky': 'HTML, CSS, JavaScript', 'en': 'HTML, CSS, JavaScript'},
      'heart-pulse', 'cyan', 2025, 10),
    P({'ru': 'DrEliyar', 'ky': 'DrEliyar', 'en': 'DrEliyar'},
      {'ru': 'Backend-система стоматологического центра: запись, заявки, Telegram-уведомления и '
             'админ-панель.',
       'ky': 'Стоматологиялык борбордун backend-системасы: жазылуу, өтүнмөлөр, Telegram-билдирүүлөр '
             'жана админ-панель.',
       'en': 'Backend system for a dental center: appointments, requests, Telegram notifications and '
             'admin panel.'},
      {'ru': 'Backend стоматологии', 'ky': 'Стоматология backend', 'en': 'Dental Clinic Backend'},
      {'ru': 'Django, Docker, PostgreSQL, Nginx', 'ky': 'Django, Docker, PostgreSQL, Nginx',
       'en': 'Django, Docker, PostgreSQL, Nginx'},
      'stethoscope', 'blue', 2025, 11),
    P({'ru': 'Solemar', 'ky': 'Solemar', 'en': 'Solemar'},
      {'ru': 'Платформа для центра отдыха с мультиязычностью, услугами, контентом и системой '
             'бронирования.',
       'ky': 'Көп тилдүүлүгү, кызматтары, мазмуну жана брондоо системасы бар эс алуу борбору үчүн '
             'платформа.',
       'en': 'Platform for a resort with multilingual content, services and a booking system.'},
      {'ru': 'Платформа для зоны отдыха', 'ky': 'Эс алуу борбору платформасы', 'en': 'Resort Platform'},
      {'ru': 'Django, PostgreSQL, Docker, JavaScript', 'ky': 'Django, PostgreSQL, Docker, JavaScript',
       'en': 'Django, PostgreSQL, Docker, JavaScript'},
      'palmtree', 'green', 2026, 12),
    P({'ru': 'AylaHostel', 'ky': 'AylaHostel', 'en': 'AylaHostel'},
      {'ru': 'Сайт и система бронирования для хостела с управлением контентом и заявками.',
       'ky': 'Мазмунду жана өтүнмөлөрдү башкаруу менен хостел үчүн сайт жана брондоо системасы.',
       'en': 'Website and booking system for a hostel with content and request management.'},
      {'ru': 'Сайт и бронирование хостела', 'ky': 'Хостел сайты жана брондоо',
       'en': 'Hostel Website & Booking'},
      {'ru': 'Django, PostgreSQL, HTML, CSS', 'ky': 'Django, PostgreSQL, HTML, CSS',
       'en': 'Django, PostgreSQL, HTML, CSS'},
      'bed', 'purple', 2025, 13),
    P({'ru': 'Merri Garden', 'ky': 'Merri Garden', 'en': 'Merri Garden'},
      {'ru': 'Платформа для площадки мероприятий с презентацией услуг, контактами и ориентированным '
             'на бронирование интерфейсом.',
       'ky': 'Кызматтардын тааныштырылышы, байланыштар жана брондоого багытталган интерфейси бар '
             'иш-чаралар аянтчасы үчүн платформа.',
       'en': 'Platform for an event venue with services presentation, contacts and a booking-oriented '
             'interface.'},
      {'ru': 'Платформа event-площадки', 'ky': 'Иш-чаралар аянтчасынын платформасы',
       'en': 'Event Venue Platform'},
      {'ru': 'Django, JavaScript, PostgreSQL', 'ky': 'Django, JavaScript, PostgreSQL',
       'en': 'Django, JavaScript, PostgreSQL'},
      'party-popper', 'orange', 2025, 14),
    P({'ru': 'Vizitka KG', 'ky': 'Vizitka KG', 'en': 'Vizitka KG'},
      {'ru': 'Информационно-рекламная digital-платформа с публикациями, журналами, голосованиями и '
             'REST API.',
       'ky': 'Жарыялар, журналдар, добуш берүүлөр жана REST API бар маалыматтык-жарнамалык санариптик '
             'платформа.',
       'en': 'Information and advertising digital platform with publications, magazines, polls and a '
             'REST API.'},
      {'ru': 'Digital-платформа медиа', 'ky': 'Санариптик медиа платформасы',
       'en': 'Digital Magazine Platform'},
      {'ru': 'Django REST Framework, PostgreSQL, Docker, Nginx',
       'ky': 'Django REST Framework, PostgreSQL, Docker, Nginx',
       'en': 'Django REST Framework, PostgreSQL, Docker, Nginx'},
      'newspaper', 'indigo', 2025, 15),
    P({'ru': 'Nurzaman', 'ky': 'Nurzaman', 'en': 'Nurzaman'},
      {'ru': 'Корпоративная digital-платформа строительной компании с презентацией объектов и услуг.',
       'ky': 'Объектилерди жана кызматтарды тааныштырган курулуш компаниясынын корпоративдик санариптик '
             'платформасы.',
       'en': 'Corporate digital platform for a construction company presenting projects and services.'},
      {'ru': 'Платформа строительной компании', 'ky': 'Курулуш компаниясынын платформасы',
       'en': 'Construction Company Platform'},
      {'ru': 'Django, PostgreSQL, HTML, CSS', 'ky': 'Django, PostgreSQL, HTML, CSS',
       'en': 'Django, PostgreSQL, HTML, CSS'},
      'building', 'blue', 2025, 16),
    P({'ru': 'KurmanjanSchool', 'ky': 'KurmanjanSchool', 'en': 'KurmanjanSchool'},
      {'ru': 'Образовательная платформа и административная система для школы.',
       'ky': 'Мектеп үчүн билим берүү платформасы жана административдик система.',
       'en': 'Educational platform and administrative system for a school.'},
      {'ru': 'Школьная платформа', 'ky': 'Мектеп платформасы', 'en': 'School Platform'},
      {'ru': 'Django, PostgreSQL', 'ky': 'Django, PostgreSQL', 'en': 'Django, PostgreSQL'},
      'graduation-cap', 'pink', 2025, 17),
    P({'ru': 'PortfolioSeitekAKA', 'ky': 'PortfolioSeitekAKA', 'en': 'PortfolioSeitekAKA'},
      {'ru': 'Современный адаптивный сайт-портфолио на Django и Docker.',
       'ky': 'Django жана Docker негизиндеги заманбап адаптивдүү портфолио-сайт.',
       'en': 'Modern responsive portfolio website built with Django and Docker.'},
      {'ru': 'Сайт-портфолио', 'ky': 'Портфолио-сайт', 'en': 'Portfolio Website'},
      {'ru': 'Django, Docker, JavaScript', 'ky': 'Django, Docker, JavaScript',
       'en': 'Django, Docker, JavaScript'},
      'briefcase', 'cyan', 2025, 18),
]
created = sum(upsert(Project, 'name', d, ('name', 'description', 'project_type', 'technologies'),
                     new_is_active=False) for d in PROJECTS)
print('Projects: создано %d (скрыты), обновлено %d' % (created, len(PROJECTS) - created))


# PARTNERS
# ─────────────────────────────────────────────────────────────
PARTNERS = [
    dict(icon='building-2', color='blue', order=1,
         name={'ru': 'Cleaning KIKI', 'ky': 'Cleaning KIKI', 'en': 'Cleaning KIKI'},
         industry={'ru': 'Клининговые услуги', 'ky': 'Клининг кызматтары', 'en': 'Cleaning Services'}),
    dict(icon='building-2', color='purple', order=2,
         name={'ru': 'AliaTex', 'ky': 'AliaTex', 'en': 'AliaTex'},
         industry={'ru': 'Швейное производство', 'ky': 'Тигүү өндүрүшү', 'en': 'Garment Production'}),
    dict(icon='zap', color='green', order=3,
         name={'ru': 'GreenEnergy', 'ky': 'GreenEnergy', 'en': 'GreenEnergy'},
         industry={'ru': 'Энергетика и IoT', 'ky': 'Энергетика жана IoT', 'en': 'Energy and IoT'}),
    dict(icon='stethoscope', color='cyan', order=4,
         name={'ru': 'DrEliyar', 'ky': 'DrEliyar', 'en': 'DrEliyar'},
         industry={'ru': 'Стоматология', 'ky': 'Стоматология', 'en': 'Dentistry'}),
    dict(icon='palmtree', color='orange', order=5,
         name={'ru': 'Solemar', 'ky': 'Solemar', 'en': 'Solemar'},
         industry={'ru': 'Туризм и отдых', 'ky': 'Туризм жана эс алуу', 'en': 'Tourism and Leisure'}),
    dict(icon='newspaper', color='indigo', order=6,
         name={'ru': 'Vizitka KG', 'ky': 'Vizitka KG', 'en': 'Vizitka KG'},
         industry={'ru': 'Медиа и реклама', 'ky': 'Медиа жана жарнама', 'en': 'Media and Advertising'}),
]
created = sum(upsert(Partner, 'name', d, ('name', 'industry'), new_is_active=False) for d in PARTNERS)
print('Partners: создано %d (скрыты), обновлено %d' % (created, len(PARTNERS) - created))


# TECH STACK
# ─────────────────────────────────────────────────────────────
def T(name, label, color, order):
    n = {'ru': name, 'ky': name, 'en': name}
    l = {'ru': label, 'ky': label, 'en': label}
    return dict(name=n, label=l, color=color, order=order)


TECH = [
    T('Django', 'Dj', 'green', 1), T('Python', 'Py', 'blue', 2),
    T('PostgreSQL', 'Pg', 'cyan', 3), T('Docker', 'Dk', 'blue', 4),
    T('REST API', 'API', 'purple', 5), T('JavaScript', 'JS', 'yellow', 6),
    T('React', 'Re', 'cyan', 7), T('Redis', 'Rd', 'red', 8),
    T('Nginx', 'Ng', 'green', 9), T('Linux', 'Lx', 'orange', 10),
    T('Git', 'Git', 'red', 11), T('Tailwind', 'Tw', 'cyan', 12),
]
created = sum(upsert(TechStack, 'name', d, ('name', 'label'), new_is_active=True) for d in TECH)
print('TechStack: создано %d, обновлено %d' % (created, len(TECH) - created))

print('=== DONE (ничего не удалено) ===')
