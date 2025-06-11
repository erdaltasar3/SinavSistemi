@echo off
echo === Sinav Sistemi Deployment Script ===
echo.

echo 1. Güncel kodları çekiyorum...
git pull

echo 2. Gereksinimleri kuruyorum...
pip install -r requirements.txt

echo 3. Statik dosyaları topluyorum...
python manage.py collectstatic --noinput

echo 4. Veritabanı migrasyonlarını uyguluyorum...
python manage.py migrate

echo 5. Gunicorn ile uygulamayı başlatıyorum...
start "Gunicorn Server" gunicorn SinavSistemi.wsgi --bind 0.0.0.0:8000 --workers 3

echo 6. Celery worker başlatılıyor...
start "Celery Worker" celery -A SinavSistemi worker --loglevel=info --pool=solo

echo 7. Celery beat başlatılıyor...
start "Celery Beat" celery -A SinavSistemi beat --loglevel=info

echo.
echo === Deployment tamamlandı! ===
echo Server şu adreste çalışıyor: http://localhost:8000/
echo. 