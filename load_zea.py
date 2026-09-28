# -*- coding: utf-8 -*-
# Загрузчик контента ZEA (ru/ky/en). Запускается через manage.py shell.
from apps.cms.models import Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings

LANGS = ['ru', 'ky', 'en']


def setml(obj, field, val):
    """Устанавливает мультиязычное поле (base + _ru/_ky/_en)."""
    setattr(obj, field, val['ru'])
    for l in LANGS:
        setattr(obj, '%s_%s' % (field, l), val[l])


# ─────────────────────────────────────────────────────────────
# SITE SETTINGS
# ─────────────────────────────────────────────────────────────
s = SiteSettings.get()
SS = {
    'site_name': {'ru': 'ZEA', 'ky': 'ZEA', 'en': 'ZEA'},
    'site_tagline': {'ru': 'IT-студия', 'ky': 'IT-студия', 'en': 'IT Studio'},
    'hero_badge': {
        'ru': 'Открыты для новых проектов',
        'ky': 'Жаңы долбоорлорго ачыкбыз',
        'en': 'Open for new projects'},
    'hero_title': {
        'ru': 'Разрабатываем цифровые решения для бизнеса',
        'ky': 'Бизнес үчүн санариптик чечимдерди иштеп чыгабыз',
        'en': 'We build digital solutions for business'},
    'hero_subtitle': {
        'ru': 'Создаём сайты, CRM-системы, Telegram-ботов и backend на Django, PostgreSQL и Docker. '
              'Помогаем бизнесу автоматизировать процессы и запускать рабочие продукты.',
        'ky': 'Сайттарды, CRM-системаларды, Telegram-botторду жана Django, PostgreSQL, Docker негизиндеги '
              'backend чечимдерди түзөбүз. Бизнеске процесстерди автоматташтырууга жана иштеген '
              'продукттарды чыгарууга жардам беребиз.',
        'en': 'We create websites, CRM systems, Telegram bots and backend solutions with Django, '
              'PostgreSQL and Docker. We help businesses automate workflows and launch working products.'},
    'about_text': {
        'ru': 'ZEA — IT-студия из Бишкека. Делаем понятные и надёжные цифровые продукты для бизнеса: '
              'от идеи и структуры до backend, дизайна, деплоя и поддержки после запуска.',
        'ky': 'ZEA — Бишкектеги IT-студия. Бизнес үчүн түшүнүктүү жана ишеничтүү санариптик продукттарды '
              'жасайбыз: идеядан жана структурадан баштап backend, дизайн, деплой жана иштеп чыккандан '
              'кийинки колдоого чейин.',
        'en': 'ZEA is an IT studio based in Bishkek. We build clear and reliable digital products for '
              'business — from idea and structure to backend, design, deployment and post-launch support.'},
    'footer_text': {
        'ru': '© 2026 ZEA IT Studio. Цифровые решения для бизнеса.',
        'ky': '© 2026 ZEA IT Studio. Бизнес үчүн санариптик чечимдер.',
        'en': '© 2026 ZEA IT Studio. Digital solutions for business.'},
    'meta_title': {
        'ru': 'ZEA IT Studio — сайты, CRM, Telegram-боты и backend-разработка',
        'ky': 'ZEA IT Studio — сайттар, CRM, Telegram-боттор жана backend иштеп чыгуу',
        'en': 'ZEA IT Studio — Websites, CRM, Telegram Bots & Backend Development'},
    'meta_description': {
        'ru': 'ZEA — IT-студия из Бишкека. Разрабатываем сайты, CRM-системы, Telegram-ботов, backend на '
              'Django/PostgreSQL/Docker и UI/UX-дизайн для бизнеса.',
        'ky': 'ZEA — Бишкектеги IT-студия. Бизнес үчүн сайттарды, CRM-системаларды, Telegram-botторду, '
              'Django/PostgreSQL/Docker backend жана UI/UX дизайнды иштеп чыгабыз.',
        'en': 'ZEA is an IT studio from Bishkek. We develop websites, CRM systems, Telegram bots, '
              'Django/PostgreSQL/Docker backend and UI/UX design for business.'},
    'meta_keywords': {
        'ru': 'ZEA, IT студия Бишкек, разработка сайтов, CRM система, Telegram бот, Django, PostgreSQL, '
              'Docker, backend, UI UX дизайн',
        'ky': 'ZEA, Бишкек IT студия, сайт жасоо, CRM система, Telegram бот, Django, PostgreSQL, Docker, '
              'backend, UI UX дизайн',
        'en': 'ZEA, IT studio Bishkek, website development, CRM system, Telegram bot, Django, PostgreSQL, '
              'Docker, backend, UI UX design'},
}
for f, v in SS.items():
    setml(s, f, v)
s.site_domain = 'https://zeastudio.su'
s.save()
print('SiteSettings: ok')


# ─────────────────────────────────────────────────────────────
# SERVICES
# ─────────────────────────────────────────────────────────────
SERVICES = [
    dict(icon='globe', color='indigo', order=1,
         title={'ru': 'Разработка сайтов', 'ky': 'Сайттарды иштеп чыгуу', 'en': 'Website Development'},
         description={
             'ru': 'Создаём лендинги, корпоративные сайты, сайты услуг и каталоги с адаптивным дизайном, '
                   'быстрой загрузкой и понятной структурой.',
             'ky': 'Адаптивдүү дизайны, тез жүктөлүшү жана түшүнүктүү структурасы бар лендингдерди, '
                   'корпоративдик сайттарды, кызмат сайттарын жана каталогдорду жасайбыз.',
             'en': 'We build landing pages, corporate sites, service websites and catalogs with responsive '
                   'design, fast loading and clear structure.'}),
    dict(icon='database', color='purple', order=2,
         title={'ru': 'CRM-системы', 'ky': 'CRM-системалар', 'en': 'CRM Systems'},
         description={
             'ru': 'Разрабатываем CRM для учёта клиентов, заказов, сотрудников, задач и отчётов под '
                   'реальные бизнес-процессы.',
             'ky': 'Кардарларды, буйрутмаларды, кызматкерлерди, тапшырмаларды жана отчётторду эсепке алуу '
                   'үчүн бизнес-процесстерге ылайык CRM иштеп чыгабыз.',
             'en': 'We develop CRM systems for managing clients, orders, staff, tasks and reports tailored '
                   'to real business processes.'}),
    dict(icon='bot', color='cyan', order=3,
         title={'ru': 'Telegram-боты', 'ky': 'Telegram-боттор', 'en': 'Telegram Bots'},
         description={
             'ru': 'Создаём ботов для заявок, уведомлений, личных кабинетов и интеграций с сайтами и CRM.',
             'ky': 'Өтүнмөлөр, билдирүүлөр, жеке кабинеттер жана сайттар менен CRM интеграциялары үчүн '
                   'ботторду түзөбүз.',
             'en': 'We create bots for requests, notifications, user accounts and integrations with '
                   'websites and CRM.'}),
    dict(icon='server', color='blue', order=4,
         title={'ru': 'Backend-разработка', 'ky': 'Backend иштеп чыгуу', 'en': 'Backend Development'},
         description={
             'ru': 'Проектируем серверную часть на Django, PostgreSQL и Docker: API, роли, базы данных, '
                   'безопасность и деплой.',
             'ky': 'Django, PostgreSQL жана Docker негизинде сервердик бөлүктү долбоорлойбуз: API, ролдор, '
                   'маалымат базалары, коопсуздук жана деплой.',
             'en': 'We design the backend on Django, PostgreSQL and Docker: APIs, roles, databases, '
                   'security and deployment.'}),
    dict(icon='layout', color='green', order=5,
         title={'ru': 'UI/UX-дизайн', 'ky': 'UI/UX дизайн', 'en': 'UI/UX Design'},
         description={
             'ru': 'Проектируем интерфейсы для сайтов, админ-панелей и внутренних систем — удобные и '
                   'понятные пользователю.',
             'ky': 'Сайттар, админ-панелдер жана ички системалар үчүн ыңгайлуу, түшүнүктүү интерфейстерди '
                   'долбоорлойбуз.',
             'en': 'We design interfaces for websites, admin panels and internal systems — convenient and '
                   'user-friendly.'}),
    dict(icon='shield-check', color='orange', order=6,
         title={'ru': 'Поддержка и развитие', 'ky': 'Колдоо жана өнүктүрүү', 'en': 'Support and Growth'},
         description={
             'ru': 'Помогаем запускать проект, исправлять ошибки, добавлять новые функции и развивать '
                   'систему после релиза.',
             'ky': 'Долбоорду ишке киргизүүгө, каталарды оңдоого, жаңы функцияларды кошууга жана релизден '
                   'кийин системаны өнүктүрүүгө жардам беребиз.',
             'en': 'We help launch projects, fix bugs, add new features and grow the system after release.'}),
]
Service.objects.all().delete()
for d in SERVICES:
    o = Service(icon=d['icon'], color=d['color'], order=d['order'], is_active=True)
    setml(o, 'title', d['title'])
    setml(o, 'description', d['description'])
    o.save()
print('Services: %d' % Service.objects.count())


# ─────────────────────────────────────────────────────────────
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
Project.objects.all().delete()
for d in PROJECTS:
    o = Project(icon=d['icon'], color=d['color'], year=d['year'], order=d['order'],
                live_url=d['live_url'], is_active=True)
    setml(o, 'name', d['name'])
    setml(o, 'description', d['description'])
    setml(o, 'project_type', d['project_type'])
    setml(o, 'technologies', d['technologies'])
    o.save()
print('Projects: %d' % Project.objects.count())


# ─────────────────────────────────────────────────────────────
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
Partner.objects.all().delete()
for d in PARTNERS:
    o = Partner(icon=d['icon'], color=d['color'], order=d['order'], is_active=True)
    setml(o, 'name', d['name'])
    setml(o, 'industry', d['industry'])
    o.save()
print('Partners: %d' % Partner.objects.count())


# ─────────────────────────────────────────────────────────────
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
TechStack.objects.all().delete()
for d in TECH:
    o = TechStack(color=d['color'], order=d['order'], is_active=True)
    setml(o, 'name', d['name'])
    setml(o, 'label', d['label'])
    o.save()
print('TechStack: %d' % TechStack.objects.count())


# ─────────────────────────────────────────────────────────────
# WHY US
# ─────────────────────────────────────────────────────────────
WHY = [
    dict(icon='check-circle', color='cyan', order=1,
         title={'ru': 'Работаем от бизнес-задачи', 'ky': 'Бизнес-маселеден баштайбыз',
                'en': 'Business-first approach'},
         description={
             'ru': 'Сначала разбираем процесс, роли пользователей и цель системы, и только потом '
                   'проектируем интерфейс и backend.',
             'ky': 'Адегенде процессти, колдонуучулардын ролдорун жана системанын максатын талдайбыз, '
                   'андан кийин гана интерфейс менен backend долбоорлойбуз.',
             'en': "We first analyze the process, user roles and the system's goal, and only then "
                   'design the interface and backend.'}),
    dict(icon='shield-check', color='green', order=2,
         title={'ru': 'Делаем рабочие системы', 'ky': 'Иштеген системаларды жасайбыз',
                'en': 'We build working systems'},
         description={
             'ru': 'Фокус не на красивой картинке, а на продукте, который принимает заявки, хранит '
                   'данные и помогает управлять бизнесом.',
             'ky': 'Көңүл сулуу сүрөткө эмес, өтүнмөлөрдү кабыл алган, маалыматтарды сактаган жана '
                   'бизнести башкарууга жардам берген продуктка бурулат.',
             'en': 'We focus not on a pretty picture but on a product that takes requests, stores data '
                   'and helps run the business.'}),
    dict(icon='rocket', color='purple', order=3,
         title={'ru': 'Запускаем поэтапно', 'ky': 'Этап-этабы менен ишке киргизебиз',
                'en': 'Step-by-step launch'},
         description={
             'ru': 'Разбиваем проект на этапы: MVP, основные функции, тестирование, запуск и '
                   'дальнейшее развитие.',
             'ky': 'Долбоорду этаптарга бөлөбүз: MVP, негизги функциялар, тестирлөө, ишке киргизүү жана '
                   'андан аркы өнүктүрүү.',
             'en': 'We split the project into stages: MVP, core features, testing, launch and further '
                   'growth.'}),
    dict(icon='server', color='blue', order=4,
         title={'ru': 'Понимаем backend и деплой', 'ky': 'Backend жана деплойду түшүнөбүз',
                'en': 'Backend and deployment expertise'},
         description={
             'ru': 'Настраиваем сервер, базу данных, Docker, домен, SSL и окружение, чтобы проект был '
                   'готов к реальной работе.',
             'ky': 'Долбоор реалдуу иштөөгө даяр болушу үчүн серверди, маалымат базасын, Docker, домен, '
                   'SSL жана чөйрөнү жөндөйбүз.',
             'en': 'We set up the server, database, Docker, domain, SSL and environment so the project '
                   'is ready for real use.'}),
    dict(icon='zap', color='orange', order=5,
         title={'ru': 'Поддерживаем после запуска', 'ky': 'Ишке киргизгенден кийин колдойбуз',
                'en': 'Support after launch'},
         description={
             'ru': 'После релиза помогаем исправлять ошибки, улучшать интерфейс и добавлять новые '
                   'функции по мере роста бизнеса.',
             'ky': 'Релизден кийин каталарды оңдоого, интерфейсти жакшыртууга жана бизнес өскөн сайын '
                   'жаңы функцияларды кошууга жардам беребиз.',
             'en': 'After release we help fix bugs, improve the interface and add new features as the '
                   'business grows.'}),
]
WhyUs.objects.all().delete()
for d in WHY:
    o = WhyUs(icon=d['icon'], color=d['color'], order=d['order'], is_active=True)
    setml(o, 'title', d['title'])
    setml(o, 'description', d['description'])
    o.save()
print('WhyUs: %d' % WhyUs.objects.count())


# ─────────────────────────────────────────────────────────────
# STATS
# ─────────────────────────────────────────────────────────────
STATS = [
    dict(icon='rocket', color='purple', order=1, is_counter=True, counter_target=3,
         value_text={'ru': '3', 'ky': '3', 'en': '3'},
         label={'ru': 'года опыта', 'ky': 'жыл тажрыйба', 'en': 'years of experience'},
         suffix={'ru': '+', 'ky': '+', 'en': '+'},
         description={'ru': 'в разработке сайтов, backend и бизнес-систем',
                      'ky': 'сайт, backend жана бизнес-системаларды иштеп чыгууда',
                      'en': 'in websites, backend and business systems'}),
    dict(icon='layers', color='indigo', order=2, is_counter=True, counter_target=18,
         value_text={'ru': '18', 'ky': '18', 'en': '18'},
         label={'ru': 'проектов', 'ky': 'долбоор', 'en': 'projects'},
         suffix={'ru': '+', 'ky': '+', 'en': '+'},
         description={'ru': 'сайты, CRM, платформы и автоматизация',
                      'ky': 'сайттар, CRM, платформалар жана автоматташтыруу',
                      'en': 'websites, CRM, platforms and automation'}),
    dict(icon='building-2', color='cyan', order=3, is_counter=True, counter_target=7,
         value_text={'ru': '7', 'ky': '7', 'en': '7'},
         label={'ru': 'сфер бизнеса', 'ky': 'бизнес тармагы', 'en': 'industries'},
         suffix={'ru': '+', 'ky': '+', 'en': '+'},
         description={'ru': 'медицина, логистика, туризм, образование, финтех, IoT, недвижимость',
                      'ky': 'медицина, логистика, туризм, билим берүү, финтех, IoT, кыймылсыз мүлк',
                      'en': 'healthcare, logistics, tourism, education, fintech, IoT, real estate'}),
    dict(icon='code-2', color='green', order=4, is_counter=False, counter_target=None,
         value_text={'ru': 'Full', 'ky': 'Full', 'en': 'Full'},
         label={'ru': 'цикл разработки', 'ky': 'цикл иштеп чыгуу', 'en': 'cycle development'},
         suffix={'ru': '', 'ky': '', 'en': ''},
         description={'ru': 'от структуры и дизайна до backend, деплоя и поддержки',
                      'ky': 'структурадан жана дизайндан backend, деплой жана колдоого чейин',
                      'en': 'from structure and design to backend, deployment and support'}),
]
Stat.objects.all().delete()
for d in STATS:
    o = Stat(icon=d['icon'], color=d['color'], order=d['order'],
             is_counter=d['is_counter'], counter_target=d['counter_target'])
    setml(o, 'value_text', d['value_text'])
    setml(o, 'label', d['label'])
    setml(o, 'suffix', d['suffix'])
    setml(o, 'description', d['description'])
    o.save()
print('Stats: %d' % Stat.objects.count())

print('=== DONE ===')
