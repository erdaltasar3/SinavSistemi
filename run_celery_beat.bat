@echo off
echo Celery Beat başlatılıyor...
celery -A SinavSistemi beat --loglevel=info 