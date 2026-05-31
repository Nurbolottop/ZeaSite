#!/bin/sh
set -e

echo "==> Ожидание PostgreSQL ($POSTGRES_HOST:$POSTGRES_PORT)..."
until nc -z "$POSTGRES_HOST" "$POSTGRES_PORT"; do
  echo "    PostgreSQL недоступен — жду 2 сек..."
  sleep 2
done
echo "==> PostgreSQL готов!"

echo "==> Применяем миграции..."
python manage.py migrate --noinput

echo "==> Компилируем переводы..."
python manage.py compilemessages || true

echo "==> Собираем статику..."
python manage.py collectstatic --noinput

echo "==> Запускаем сервер..."
exec "$@"
