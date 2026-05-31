from django.core.management.base import BaseCommand
from apps.cms.models import Service, Project, Partner, TechStack, WhyUs, Stat, SiteSettings


class Command(BaseCommand):
    help = 'Заполняет базу данных начальными данными для сайта ZEA'

    def handle(self, *args, **options):
        self.stdout.write('Заполнение базы данных...')

        # ── SiteSettings ──────────────────────────────────────────────
        settings, _ = SiteSettings.objects.get_or_create(pk=1)
        settings.hero_badge    = 'Открыты для новых проектов'
        settings.hero_title    = 'ZEA — разработка цифровых решений для бизнеса'
        settings.hero_subtitle = ('Создаём сайты, CRM-системы, Telegram-ботов и внутренние '
                                   'платформы для автоматизации бизнес-процессов.')
        settings.about_text    = ('ZEA — мини IT-студия, которая помогает бизнесам запускать '
                                   'современные цифровые продукты. Мы разрабатываем сайты, '
                                   'CRM-системы, Telegram-ботов и решения для автоматизации '
                                   'процессов.')
        settings.telegram_url  = 'https://t.me/zea_studio'
        settings.whatsapp_url  = 'https://wa.me/996700000000'
        settings.instagram_url = 'https://instagram.com/zea.studio'
        settings.email         = 'hello@zea.dev'
        settings.save()
        self.stdout.write('  ✓ SiteSettings')

        # ── Services ──────────────────────────────────────────────────
        Service.objects.all().delete()
        services_data = [
            dict(title='Разработка сайтов',
                 description='Landing Page, корпоративные сайты, сайты услуг, каталоги.',
                 icon='globe', color='indigo', order=1),
            dict(title='CRM-системы',
                 description='Учёт клиентов, заказов, сотрудников, отчёты и аналитика.',
                 icon='database', color='purple', order=2),
            dict(title='Telegram-боты',
                 description='Заявки, уведомления, личные кабинеты, интеграции.',
                 icon='send', color='cyan', order=3),
            dict(title='Backend-разработка',
                 description='Django, REST API, PostgreSQL, Docker.',
                 icon='server', color='blue', order=4),
            dict(title='UI/UX дизайн',
                 description='Интерфейсы, админ-панели, дизайн веб-сервисов.',
                 icon='layout', color='pink', order=5),
        ]
        for d in services_data:
            Service.objects.create(**d)
        self.stdout.write(f'  ✓ Services ({len(services_data)})')

        # ── Projects ──────────────────────────────────────────────────
        Project.objects.all().delete()
        projects_data = [
            dict(name='Cleaning KIKI',
                 description='CRM-система и сайт для клининговой компании. Учёт клиентов, '
                              'заказов и автоматические уведомления.',
                 project_type='CRM + Website',
                 technologies='Django, PostgreSQL, React, Docker',
                 icon='sparkles', color='indigo', year=2024, order=1),
            dict(name='KIKI Academy',
                 description='Платформа для обучения сотрудников компании с системой курсов, '
                              'тестирования и аналитикой прогресса.',
                 project_type='LMS Platform',
                 technologies='Django, REST API, Docker, Linux',
                 icon='graduation-cap', color='purple', year=2024, order=2),
            dict(name='AliaTex',
                 description='Корпоративный сайт для швейного производства с каталогом '
                              'продукции и онлайн-формой заявок.',
                 project_type='Corporate Site',
                 technologies='Django, JavaScript, Tailwind',
                 icon='shirt', color='cyan', year=2023, order=3),
            dict(name='GreenEnergy',
                 description='IoT-платформа для мониторинга электроэнергии с дашбордами '
                              'и аналитикой в реальном времени.',
                 project_type='IoT Platform',
                 technologies='Python, Django, React, Docker',
                 icon='zap', color='green', year=2024, order=4),
        ]
        for d in projects_data:
            Project.objects.create(**d)
        self.stdout.write(f'  ✓ Projects ({len(projects_data)})')

        # ── Partners ──────────────────────────────────────────────────
        Partner.objects.all().delete()
        partners_data = [
            dict(name='Cleaning KIKI', industry='Клининг',    icon='sparkles',      color='indigo', order=1),
            dict(name='AliaTex',       industry='Производство', icon='shirt',        color='cyan',   order=2),
            dict(name='KIKI Academy',  industry='Образование', icon='graduation-cap', color='purple', order=3),
            dict(name='GreenEnergy',   industry='Энергетика',  icon='zap',           color='green',  order=4),
        ]
        for d in partners_data:
            Partner.objects.create(**d)
        self.stdout.write(f'  ✓ Partners ({len(partners_data)})')

        # ── TechStack ─────────────────────────────────────────────────
        TechStack.objects.all().delete()
        tech_data = [
            dict(name='Python',     label='Py',  color='yellow', order=1),
            dict(name='Django',     label='Dj',  color='green',  order=2),
            dict(name='PostgreSQL', label='Pg',  color='blue',   order=3),
            dict(name='Docker',     label='Dk',  color='cyan',   order=4),
            dict(name='JavaScript', label='JS',  color='yellow', order=5),
            dict(name='React',      label='Re',  color='cyan',   order=6),
            dict(name='Next.js',    label='Nx',  color='indigo', order=7),
            dict(name='REST API',   label='API', color='orange', order=8),
            dict(name='Linux',      label='Lx',  color='indigo', order=9),
            dict(name='Git',        label='Git', color='red',    order=10),
        ]
        for d in tech_data:
            TechStack.objects.create(**d)
        self.stdout.write(f'  ✓ TechStack ({len(tech_data)})')

        # ── WhyUs ─────────────────────────────────────────────────────
        WhyUs.objects.all().delete()
        why_data = [
            dict(title='Понимаем бизнес-задачи',
                 description='Погружаемся в процессы бизнеса, чтобы предложить точное решение, а не шаблон.',
                 icon='target', color='indigo', order=1),
            dict(title='Рабочий инструмент',
                 description='Делаем не просто сайт, а инструмент, который реально работает и приносит деньги.',
                 icon='wrench', color='purple', order=2),
            dict(title='Быстрый запуск MVP',
                 description='Запускаем минимально жизнеспособный продукт быстро, чтобы вы тестировали рынок.',
                 icon='rocket', color='cyan', order=3),
            dict(title='Поддержка после запуска',
                 description='Не бросаем проект — сопровождаем, дорабатываем и развиваем.',
                 icon='shield-check', color='green', order=4),
            dict(title='Гибкая разработка',
                 description='Работаем итеративно — вы видите прогресс и участвуете в процессе на каждом этапе.',
                 icon='git-branch', color='blue', order=5),
        ]
        for d in why_data:
            WhyUs.objects.create(**d)
        self.stdout.write(f'  ✓ WhyUs ({len(why_data)})')

        # ── Stats ─────────────────────────────────────────────────────
        Stat.objects.all().delete()
        stats_data = [
            dict(value_text='3', label='Года опыта',           suffix='+', is_counter=True,  counter_target=3,  order=1),
            dict(value_text='5', label='Проектов сдано',       suffix='+', is_counter=True,  counter_target=5,  order=2),
            dict(value_text='CRM / Bot', label='Сайты & боты', suffix='',  is_counter=False, order=3),
            dict(value_text='Полный цикл разработки', label='', suffix='', is_counter=False, icon='refresh-cw', order=4),
        ]
        for d in stats_data:
            Stat.objects.create(**d)
        self.stdout.write(f'  ✓ Stats ({len(stats_data)})')

        self.stdout.write(self.style.SUCCESS('\n✅ База данных успешно заполнена!'))
