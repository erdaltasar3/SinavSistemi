@echo off
echo Celery Worker başlatılıyor...
celery -A SinavSistemi worker --loglevel=info --pool=solo 