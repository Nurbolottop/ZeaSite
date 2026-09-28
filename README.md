# ZEA — IT Studio

Публичный сайт **ZEA** — технологического партнёра для бизнеса (два формата: технологическое партнёрство и разработка под заказ) — и внутренняя система ZEA Hub (`/hub/`).

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
- **Frontend:** серверный рендеринг Django Templates + Tailwind CSS v3 (собирается из репозитория, см. ниже), Lucide icons, AOS
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
├── frontend/                  # исходник Tailwind + reference/ (копия прежнего production CSS)
├── docker/                    # Dockerfile + docker-compose (dev/prod)
├── package.json               # сборка Tailwind (npm run build:css)
├── tailwind.config.js         # content — только публичные шаблоны
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
python manage.py makemessages -l ru -l ky -l en --ignore=staticfiles --ignore=static \
  --ignore='apps/hub/*' --ignore='apps/users/*' --ignore='apps/partners/*' \
  --ignore='apps/contracts/*' --ignore='apps/projects/*' --ignore='apps/team/*' \
  --ignore='templates/hub/*' --ignore='templates/partners/*' --ignore='templates/contracts/*' \
  --ignore='templates/projects/*' --ignore='templates/team/*'
python manage.py compilemessages
```

Перевод полей моделей (услуги, проекты и т.д.) — через вкладки языков в админке.

---

## Публичный сайт: Tailwind CSS

Стили главной — Tailwind **v3** (не v4). Собранный файл `app/static/css/tailwind.css`
**хранится в git**, поэтому Node на сервере не нужен и стили есть на чистом clone.
Вьюха встраивает его в `<style>`: сначала из `STATIC_ROOT` (после collectstatic),
иначе из `app/static` через staticfiles finders.

После изменения классов в публичных шаблонах (`templates/index.html`, `templates/site/**`):

```bash
npm ci                 # один раз (tailwindcss 3.4.17)
npm run build:css      # → app/static/css/tailwind.css (минифицирован), закоммитить
npm run watch:css      # при разработке
```

Шаблоны ZEA Hub (Bootstrap) в сборку не входят. `frontend/reference/` — копия CSS,
который был на production до переноса сборки в репозиторий (для сравнения).

---

## Публичный сайт: контент

- Структура главной: Hero → О ZEA + «Что мы берём на себя» → Форматы сотрудничества →
  Как мы начинаем работу → Направления (+ стек) → Проекты* → Цифры* и Партнёры* →
  Почему ZEA → Контакты и заявка. *Секции скрываются, пока нет активных записей.
- Всё редактируется в админке: раздел «Публичный сайт (контент)».
- Утверждённые тексты (RU/KY/EN) лежат в `apps/cms/site_content.py`. Миграция
  `cms/0010` один раз заполняет ими пустые блоки; повторно —
  `python manage.py populate_db` (создаёт недостающее) или `populate_db --update`
  (перезаписывает тексты). **Ничего не удаляет.** Проекты, партнёров и статистику
  не создаёт — только реальные данные вручную.
- `load_zea.py` — черновики портфолио: создаёт проекты и партнёров **скрытыми**,
  без удаления. Не запускать на production без отдельного решения.
- Заявки: тип обращения, направление, компания и сфера пока дописываются в начало
  текста заявки (без миграции `contacts`).

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
