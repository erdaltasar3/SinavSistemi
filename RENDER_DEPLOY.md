# Render.com ile Sınav Sistemi Deployment

Bu projeyi Render.com'un ücretsiz planında deploy etmek için hazırlanan dosyalardır.

## Hazırlanan Dosyalar

1. `render.yaml`: Render.com konfigürasyonu
2. `Procfile`: Web sunucusu yapılandırması
3. `runtime.txt`: Python versiyonu
4. `build.sh`: Build ve deployment script
5. `core/management/commands/init_render_db.py`: Veritabanı başlatma komutu

## Render.com Dashboard Adımları

1. Render.com hesabı oluşturun
2. "New +" > "Blueprint" seçeneğini tıklayın
3. GitHub hesabınızı bağlayın
4. Repo'nuzu seçin ve "Connect" butonuna tıklayın
5. Render.yaml dosyası otomatik olarak algılanacaktır
6. "Create Blueprint" butonuna tıklayın

## Ek Yapılandırma

### E-posta Şifresi

Email sistemi için Gmail App şifresini Environment Variables içine manuel olarak eklemeniz gerekecektir:

1. Render Dashboard > Environment kısmından "EMAIL_HOST_PASSWORD" değişkenini ekleyin
2. Değer olarak Gmail App şifrenizi girin

### Veritabanı ve İçerik

Ücretsiz planda PostgreSQL veritabanı 90 gün sonra silinecektir.
Yeni veriler eklendiğinde yeni bir dump alarak initial_data.json'u güncelleyin.

## Celery ve Background Tasks

Render.com ücretsiz planında Celery kullanımı desteklenmemektedir. Bu nedenle:

- CELERY_TASK_ALWAYS_EAGER = True ayarı ile tüm tasklar senkron çalışacaktır
- Ücretsiz planda Redis yoktur, bu yüzden SQLite backend kullanılmaktadır

## Statik ve Medya Dosyaları

- Statik dosyalar Whitenoise ile sunulmaktadır
- Medya dosyaları kalıcı olmayacaktır (ücretsiz plan için)

## Sorun Giderme

- Hataları Render Dashboard üzerinden görebilirsiniz
- Günlükleri "Logs" sekmesinden takip edebilirsiniz
- Veritabanına pgAdmin ile bağlanabilirsiniz (bağlantı bilgilerini Render Dashboard'dan alın)

## Sınırlamalar

Render'ın ücretsiz planı aşağıdaki sınırlamalara sahiptir:
- Her ay 750 saat free tier saatiniz var
- İnaktif olduktan 15 dakika sonra uygulamanız uyku moduna geçer
- Kalıcı disk depolama yok - her deploy'da dosyalar silinir
- PostgreSQL veritabanı 90 gün sonra silinir ve yeniden oluşturulması gerekir 