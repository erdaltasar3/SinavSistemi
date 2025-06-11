import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import connections
from django.db.utils import OperationalError
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Veritabanını ve verileri Render.com üzerinde başlatır'

    def handle(self, *args, **kwargs):
        # Veritabanına bağlanma kontrolü
        self.stdout.write('Veritabanı bağlantısı kontrol ediliyor...')
        db_conn = connections['default']
        try:
            db_conn.cursor()
            self.stdout.write(self.style.SUCCESS('Veritabanı bağlantısı başarılı.'))
        except OperationalError:
            self.stdout.write(self.style.ERROR('Veritabanına bağlanılamadı!'))
            return

        # Kullanıcı kontrolü
        self.stdout.write('Veritabanında kullanıcı kontrolü yapılıyor...')
        if User.objects.exists():
            self.stdout.write(self.style.SUCCESS('Veritabanında zaten kullanıcılar var, veri yükleme atlanıyor.'))
            return
        
        # Migrasyonları uygula
        self.stdout.write('Migrasyonlar uygulanıyor...')
        call_command('migrate')
        
        # Fixture dosyasını yükle
        fixture_path = os.path.join(os.getcwd(), 'initial_data.json')
        if os.path.exists(fixture_path):
            self.stdout.write(f'Verileri {fixture_path} dosyasından yüklüyorum...')
            try:
                call_command('loaddata', fixture_path)
                self.stdout.write(self.style.SUCCESS('Veriler başarıyla yüklendi!'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Veri yüklerken hata: {str(e)}'))
        else:
            self.stdout.write(self.style.WARNING(f'Veri dosyası bulunamadı: {fixture_path}'))
            
            # Veri dosyası bulunamazsa, test admin kullanıcısı oluştur
            self.stdout.write('Test admin kullanıcısı oluşturuluyor...')
            try:
                User.objects.create_superuser('admin', 'admin@example.com', 'Admin.123')
                self.stdout.write(self.style.SUCCESS('Admin kullanıcısı oluşturuldu (admin/Admin.123)'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Admin kullanıcısı oluşturma hatası: {str(e)}')) 