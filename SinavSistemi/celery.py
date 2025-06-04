import os

from celery import Celery

# Celery programı için varsayılan Django ayarları modülünü ayarla.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'SinavSistemi.settings')

# Celery uygulamasını oluştur ve yapılandır.
app = Celery('SinavSistemi')

# Django ayarlarındaki Celery yapılandırmasını yükle.
# Namespace='CELERY' yaparak tüm celery ilgili ayarların 'CELERY_' ile başlamasını sağlıyoruz.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Uygulama kayıtlı taskları (görevleri) otomatik olarak bulur.
# Uygulamalarınızdaki tasks.py dosyalarını arar.
app.autodiscover_tasks()

# Task hata ayıklama (debug) ayarları için örnek task.
@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}') 