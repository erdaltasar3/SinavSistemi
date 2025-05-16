from django.core.management.base import BaseCommand
from django.utils import timezone
from yks.models import YKSOturum

class Command(BaseCommand):
    help = 'Sınav tarihine göre oturum durumlarını günceller'
    
    def handle(self, *args, **options):
        # Tüm oturumları al
        oturumlar = YKSOturum.objects.all()
        guncellenen_sayisi = 0
        
        for oturum in oturumlar:
            if oturum.sinav_tarihi:
                # Timezone bilgisini kontrol et
                if timezone.is_naive(oturum.sinav_tarihi):
                    sinav_tarihi = timezone.make_aware(oturum.sinav_tarihi)
                else:
                    sinav_tarihi = oturum.sinav_tarihi
                
                # Sınav tarihi geçmişse durum "Geçmiş" olarak güncelle
                eski_durum = oturum.durum
                if sinav_tarihi < timezone.now() and oturum.durum != YKSOturum.DURUM_GECMIS:
                    oturum.durum = YKSOturum.DURUM_GECMIS
                    oturum.save(update_fields=['durum'])
                    guncellenen_sayisi += 1
                    self.stdout.write(f'Oturum güncellendi: {oturum.ad} ({oturum.yil}) - {eski_durum} -> {oturum.durum}')
                elif sinav_tarihi >= timezone.now() and oturum.durum != YKSOturum.DURUM_BEKLIYOR:
                    oturum.durum = YKSOturum.DURUM_BEKLIYOR
                    oturum.save(update_fields=['durum'])
                    guncellenen_sayisi += 1
                    self.stdout.write(f'Oturum güncellendi: {oturum.ad} ({oturum.yil}) - {eski_durum} -> {oturum.durum}')
        
        self.stdout.write(self.style.SUCCESS(f'Toplam {guncellenen_sayisi} oturum güncellendi.')) 