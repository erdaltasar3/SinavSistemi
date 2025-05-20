from django.core.management.base import BaseCommand
from core.models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu,
    HedefTuru, HedefDurumu
)

class Command(BaseCommand):
    help = 'Uygulama için başlangıç verilerini yükler'

    def handle(self, *args, **options):
        # Hedef türlerini oluştur
        self.stdout.write('Hedef türleri oluşturuluyor...')
        hedef_turleri = [
            {'ad': 'Günlük', 'sira_no': 1},
            {'ad': 'Haftalık', 'sira_no': 2},
            {'ad': 'Aylık', 'sira_no': 3},
            {'ad': 'Dönemlik', 'sira_no': 4},
            {'ad': 'Yıllık', 'sira_no': 5},
        ]
        
        for tur in hedef_turleri:
            HedefTuru.objects.get_or_create(
                ad=tur['ad'],
                defaults={'sira_no': tur['sira_no']}
            )
        
        # Hedef durumlarını oluştur
        self.stdout.write('Hedef durumları oluşturuluyor...')
        hedef_durumlari = [
            {'ad': 'Planlandı', 'renk': 'secondary', 'sira_no': 1},
            {'ad': 'Devam Ediyor', 'renk': 'primary', 'sira_no': 2},
            {'ad': 'Tamamlandı', 'renk': 'success', 'sira_no': 3},
            {'ad': 'Gecikti', 'renk': 'danger', 'sira_no': 4},
            {'ad': 'Ertelendi', 'renk': 'warning', 'sira_no': 5},
            {'ad': 'İptal Edildi', 'renk': 'dark', 'sira_no': 6},
        ]
        
        for durum in hedef_durumlari:
            HedefDurumu.objects.get_or_create(
                ad=durum['ad'],
                defaults={
                    'renk': durum['renk'],
                    'sira_no': durum['sira_no']
                }
            )
        
        self.stdout.write(self.style.SUCCESS('Başlangıç verileri başarıyla yüklendi.')) 