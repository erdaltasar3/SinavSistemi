# Hatırlatıcı E-posta Sistemi Kurulumu

Bu projede, kullanıcıların belirledikleri tarih ve saatte otomatik e-posta hatırlatıcıları alabilmeleri için Celery ve SQLite backend kullanılmaktadır.

## Kurulum Adımları

1. Gerekli kütüphaneleri yükleyin:
```bash
pip install celery sqlalchemy==1.4.47 sqlalchemy-utils django-celery-beat
```

2. Celery worker'ı başlatın:
```bash
# Windows'ta
run_celery.bat

# Linux/Mac'te
celery -A SinavSistemi worker --loglevel=info
```

3. Celery beat (zamanlayıcı) başlatın:
```bash
# Windows'ta
run_celery_beat.bat

# Linux/Mac'te
celery -A SinavSistemi beat --loglevel=info
```

## Kullanım

1. Hatırlatıcılar sayfasından yeni bir hatırlatıcı ekleyin
2. Hatırlatma tarihi ve saati geldiğinde, sistem otomatik olarak e-posta gönderecektir
3. E-posta başlığı hatırlatıcı başlığı, içeriği ise hatırlatıcı açıklaması olacaktır

## Sorun Giderme

- E-posta gönderilmiyorsa:
  - Celery worker'ın çalıştığından emin olun
  - E-posta ayarlarının doğru olduğunu kontrol edin
  - Hatırlatıcının aktif olduğundan emin olun
  - Celery günlük dosyasını kontrol edin

- Zamanlanmış görevler çalışmıyorsa:
  - Celery beat'in çalıştığından emin olun
  - Sistem saatini kontrol edin
  - Celery beat günlük dosyasını kontrol edin 