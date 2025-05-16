from django.core.management.base import BaseCommand
from core.models import SinavTurleri, SinavAltTur, Ders

class Command(BaseCommand):
    help = 'Örnek sınav alt türleri ve dersler ekler'
    
    def handle(self, *args, **options):
        self.stdout.write('Örnek veri ekleniyor...')
        
        # YKS sınav türünü bul ya da oluştur
        yks, _ = SinavTurleri.objects.get_or_create(
            kod='YKS',
            defaults={
                'ad': 'Yükseköğretim Kurumları Sınavı',
                'aciklama': 'Üniversiteye giriş için yapılan merkezi sınav.',
                'ikon': 'mortarboard',
                'url': '/yks/',
                'aktif': True
            }
        )
        
        # YKS Alt Türlerini ekle
        alt_turler = [
            {
                'kod': 'TYT',
                'ad': 'Temel Yeterlilik Testi',
                'aciklama': 'Türkçe, matematik, fen bilimleri ve sosyal bilimler testlerinden oluşan oturum.',
                'ikon': 'journal-check'
            },
            {
                'kod': 'AYT',
                'ad': 'Alan Yeterlilik Testi',
                'aciklama': 'Matematik, fen bilimleri, Türk dili ve edebiyatı, sosyal bilimler testlerinden oluşan oturum.',
                'ikon': 'compass'
            },
            {
                'kod': 'YDT',
                'ad': 'Yabancı Dil Testi',
                'aciklama': 'Yabancı dil yeterliliklerini ölçen oturum.',
                'ikon': 'translate'
            }
        ]
        
        created_alt_turler = {}
        
        for alt_tur_data in alt_turler:
            alt_tur, created = SinavAltTur.objects.update_or_create(
                sinav_turu=yks,
                kod=alt_tur_data['kod'],
                defaults={
                    'ad': alt_tur_data['ad'],
                    'aciklama': alt_tur_data['aciklama'],
                    'ikon': alt_tur_data.get('ikon'),
                    'aktif': True
                }
            )
            
            created_alt_turler[alt_tur_data['kod']] = alt_tur
            
            if created:
                self.stdout.write(self.style.SUCCESS(f"{alt_tur.ad} alt türü eklendi."))
            else:
                self.stdout.write(f"{alt_tur.ad} alt türü güncellendi.")
        
        # Dersleri ekle
        ders_verileri = {
            'TYT': [
                {'kod': 'MAT', 'ad': 'Matematik', 'ikon': 'calculator', 'aciklama': 'TYT Matematik dersi'},
                {'kod': 'TUR', 'ad': 'Türkçe', 'ikon': 'book', 'aciklama': 'TYT Türkçe dersi'},
                {'kod': 'TAR', 'ad': 'Tarih', 'ikon': 'hourglass', 'aciklama': 'TYT Tarih dersi'},
                {'kod': 'COG', 'ad': 'Coğrafya', 'ikon': 'globe', 'aciklama': 'TYT Coğrafya dersi'},
                {'kod': 'FIZ', 'ad': 'Fizik', 'ikon': 'lightning', 'aciklama': 'TYT Fizik dersi'},
                {'kod': 'KIM', 'ad': 'Kimya', 'ikon': 'droplet', 'aciklama': 'TYT Kimya dersi'}
            ],
            'AYT': [
                {'kod': 'MAT', 'ad': 'Matematik', 'ikon': 'calculator', 'aciklama': 'AYT Matematik dersi'},
                {'kod': 'GEO', 'ad': 'Geometri', 'ikon': 'triangle', 'aciklama': 'AYT Geometri dersi'},
                {'kod': 'FIZ', 'ad': 'Fizik', 'ikon': 'lightning', 'aciklama': 'AYT Fizik dersi'},
                {'kod': 'KIM', 'ad': 'Kimya', 'ikon': 'droplet', 'aciklama': 'AYT Kimya dersi'},
                {'kod': 'BIY', 'ad': 'Biyoloji', 'ikon': 'tree', 'aciklama': 'AYT Biyoloji dersi'},
                {'kod': 'EDBI', 'ad': 'Türk Dili ve Edebiyatı', 'ikon': 'book', 'aciklama': 'AYT Türk Dili ve Edebiyatı dersi'}
            ],
            'YDT': [
                {'kod': 'ING', 'ad': 'İngilizce', 'ikon': 'translate', 'aciklama': 'YDT İngilizce dersi'},
                {'kod': 'ALM', 'ad': 'Almanca', 'ikon': 'translate', 'aciklama': 'YDT Almanca dersi'},
                {'kod': 'FRA', 'ad': 'Fransızca', 'ikon': 'translate', 'aciklama': 'YDT Fransızca dersi'}
            ]
        }
        
        # Dersleri ekle
        ders_sayisi = 0
        
        for alt_tur_kod, dersler in ders_verileri.items():
            alt_tur = created_alt_turler.get(alt_tur_kod)
            
            if alt_tur:
                for ders_data in dersler:
                    ders, created = Ders.objects.update_or_create(
                        alt_tur=alt_tur,
                        kod=ders_data['kod'],
                        defaults={
                            'ad': ders_data['ad'],
                            'aciklama': ders_data.get('aciklama', ''),
                            'ikon': ders_data.get('ikon', ''),
                            'aktif': True
                        }
                    )
                    
                    if created:
                        ders_sayisi += 1
        
        self.stdout.write(self.style.SUCCESS(f"Toplam {ders_sayisi} ders eklendi."))
        self.stdout.write(self.style.SUCCESS('İşlem tamamlandı.')) 