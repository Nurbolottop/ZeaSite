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
│   │   ├── contacts/          # форма заявок
│   │   ├── hub/               # ZEA Hub: layout, меню, Dashboard, защита /hub/
│   │   ├── users/             # ZEA Hub: роли (Groups), HubProfile, проверка доступа
│   │   ├── partners/          # ZEA Hub: компании — кандидаты и партнёры (/hub/candidates/, /hub/partners/)
│   │   └── contracts/         # ZEA Hub: договоры партнёрства и документы (/hub/contracts/)
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

Контейнер автоматически применяет миграции и собирает статику. Сайт: **http://localhost:8086**, Hub: **http://localhost:8086/hub/**, админка: **http://localhost:8086/admin**

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

---

## ZEA Hub (`/hub/`)

Закрытая внутренняя система команды в том же Django-проекте и той же БД, что и сайт.

- `/hub/` — Dashboard, `/hub/login/`, `/hub/logout/`, все будущие модули — только под `/hub/`.
- `HubLoginRequiredMiddleware` требует вход для любого URL под `/hub/`; публичный сайт не затрагивается.
- Пользователь — стандартный `auth.User` (AUTH_USER_MODEL не меняется), данные сотрудника — `users.HubProfile`.
- Роли — 6 Django Groups (миграция `users/0002_create_roles`), имена в `apps/users/roles.py`.
  Матрица доступа к разделам — `MODULE_ACCESS` в `apps/users/access.py`; во view — `RoleRequiredMixin`.
- Бизнес-логика модулей — в `services.py` / `selectors.py`, views тонкие. Статус компании меняется только
  через `apps.partners.services.change_status()` (проверка перехода + история).
- Права на действия — `PERMISSIONS` в `apps/users/access.py` (`partners.*`, `contracts.view/manage/activate/
  view_financial_terms`). Критичные для денег проверки (активация, финансовые поля) — ещё и в services.
- Партнёром компания становится только действием «Оформить как партнёра» при ACTIVE-договоре.
- Шаблоны Hub — `templates/hub/`, стили — `static/hub/hub.css` (Bootstrap 5 с CDN). На сайт не подключаются.
- Приватные файлы (договоры) — `private_media/` вне `MEDIA_ROOT`, без публичного URL (`apps.hub.storage`).
  Физические имена — UUID, скачивание только через `/hub/contracts/.../download/` с проверкой прав.
  Для этой папки **не** настраивать отдачу через nginx. Лимит файла — 20 МБ (учесть `client_max_body_size` в nginx).

Локальная разработка Hub: `docker compose -f docker/docker-compose.yml up --build` →
http://localhost:8086 (сайт) и http://localhost:8086/hub/ (Hub), БД `localhost:5434`.
Тесты: `docker exec django_web_hub python manage.py test`.
