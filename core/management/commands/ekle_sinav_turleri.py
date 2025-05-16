from django.core.management.base import BaseCommand
from core.models import SinavTurleri

class Command(BaseCommand):
    help = 'Varsayılan sınav türlerini ekler'
    
    def handle(self, *args, **options):
        self.stdout.write('Varsayılan sınav türleri ekleniyor...')
        
        # YKS Sınav türünü ekleme
        yks, created = SinavTurleri.objects.get_or_create(
            kod='YKS',
            defaults={
                'ad': 'Yükseköğretim Kurumları Sınavı',
                'aciklama': 'Üniversiteye giriş için yapılan merkezi sınav.',
                'ikon': 'mortarboard',  # Bootstrap ikonu
                'url': '/yks/',
                'aktif': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'YKS sınav türü başarıyla eklendi.'))
        else:
            self.stdout.write(f'YKS sınav türü zaten mevcut.')
            
        self.stdout.write(self.style.SUCCESS('İşlem tamamlandı.')) 