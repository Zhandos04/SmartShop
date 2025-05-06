#!/bin/bash
set -e

# Ожидаем готовности PostgreSQL
until pg_isready -h db -p 5432; do
  >&2 echo "PostgreSQL еще не готов - ждем..."
  sleep 1
done

>&2 echo "PostgreSQL готов - продолжаем..."

# Создаем директорию для статических файлов, если ее нет
mkdir -p /app/staticfiles
echo "Директория для статических файлов создана или уже существует"

# Собираем статические файлы
python manage.py collectstatic --noinput

# Применяем миграции
python manage.py makemigrations
python manage.py migrate

# Создаем суперпользователя, если его нет
python manage.py shell -c "
from django.contrib.auth import get_user_model;
User = get_user_model();
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123456');
    print('Суперпользователь создан');
else:
    print('Суперпользователь уже существует');
"

# Загружаем начальные данные
python manage.py loaddata initial_data.json || echo "Нет начальных данных для загрузки"

# Запускаем сервер
exec python manage.py runserver 0.0.0.0:8000