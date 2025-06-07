import os
from celery import Celery
from celery.signals import task_success, task_failure

# Django settings modülünü ayarla
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SinavSistemi.settings')

# Celery uygulamasını oluştur
app = Celery('SinavSistemi')

# Django ayarlarından konfigürasyon al (CELERY_ ile başlayanlar)
app.config_from_object('django.conf:settings', namespace='CELERY')

# Task'ları otomatik keşfet
app.autodiscover_tasks()

# Başarılı task sonuçlarını logla
@task_success.connect
def task_success_handler(sender=None, **kwargs):
    print(f"✅ Görev başarıyla tamamlandı: {sender.name} (ID: {kwargs.get('task_id')})")

# Başarısız task sonuçlarını logla
@task_failure.connect
def task_failure_handler(sender=None, **kwargs):
    print(f"❌ Görev hatası: {sender.name} (ID: {kwargs.get('task_id')})")
    print(f"   Hata: {kwargs.get('exception')}")

# Debug için örnek görev
@app.task(bind=True)
def debug_task(self):
    print(f'Debug görevi çalışıyor: {self.request!r}') 