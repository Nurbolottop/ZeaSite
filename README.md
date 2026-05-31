# ZEA — IT Studio

Сайт-портфолио IT-студии **ZEA**: разработка сайтов, CRM-систем, Telegram-ботов и решений для автоматизации бизнеса.

Одностраничный сайт на Django с полноценной CMS-админкой, поддержкой 3 языков и профессиональной SEO-оптимизацией.

---

## Возможности

- **CMS-админка** — весь контент (услуги, проекты, партнёры, стек, статистика, настройки) редактируется через админ-панель Django без правки кода
- **3 языка** — русский, кыргызский, английский ([django-modeltranslation](https://django-modeltranslation.readthedocs.io/)), переключение через AJAX без перезагрузки
- **Языковые URL** — `/` (ru), `/ky/`, `/en/` для корректной индексации поисковиками
- **Форма заявок** — AJAX-отправка с сохранением в БД и просмотром в админке
- **SEO** — canonical, hreflang, Open Graph, Twitter Cards, JSON-LD (Organization), sitemap.xml, robots.txt, GA4 + Search Console (настраивается в админке)
- **Кастомные страницы 404/500** в фирменном стиле
- **Docker** — dev и prod конфигурации

## Технологии

- **Backend:** Django 5.2, PostgreSQL
- **Frontend:** серверный рендеринг Django Templates + Tailwind CSS (CDN), Lucide icons, AOS
- **Изображения:** django-resized (автоконвертация в WebP)
- **Контент:** django-ckeditor
- **Инфраструктура:** Docker / docker-compose

---

## Структура

```
ZEA/
├── app/                       # Django проект
│   ├── apps/
│   │   ├── base/              # главная страница, sitemap, robots
│   │   ├── cms/               # модели контента + админка + переводы
│   │   └── contacts/          # форма заявок
│   ├── core/settings/         # base / dev / prod
│   ├── templates/             # index.html, 404, 500, админ-шаблоны
│   ├── locale/                # переводы ru/ky/en
│   └── static/
├── docker/                    # Dockerfile + docker-compose (dev/prod)
├── scripts/entrypoint.sh
├── requirements.txt
└── .envtest                   # пример переменных окружения
```

---

## Запуск (Docker)

1. Создать `.env` на основе примера:

```bash
cp .envtest .env
```

Заполнить минимум: `SECRET_KEY`, `POSTGRES_*`, `ALLOWED_HOSTS`.

2. Запустить dev-сборку:

```bash
docker compose -f docker/docker-compose.yml up --build
```

Контейнер автоматически применяет миграции и собирает статику. Сайт: **http://localhost:8085**, админка: **http://localhost:8085/admin**

### Продакшн

```bash
docker compose -f docker/docker-compose.prod.yml up --build -d
```

В prod Django работает через gunicorn.

---

## Переводы

После изменения строк в шаблонах/коде:

```bash
python manage.py makemessages -l ru -l ky -l en --ignore=staticfiles --ignore=static
python manage.py compilemessages
```

Перевод полей моделей (услуги, проекты и т.д.) — через вкладки языков в админке.

---

## SEO-настройка после деплоя

1. Вписать реальный домен в **Админка → Настройки сайта → Аналитика и индексация**
2. Подтвердить сайт в Google Search Console, отправить `sitemap.xml`
3. Создать GA4-ресурс, вписать `G-XXXX` ID
4. Наполнять контентом (кейсы, статьи) — основной источник органического трафика
