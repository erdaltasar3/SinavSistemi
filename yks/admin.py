from django.contrib import admin
from .models import (
    YKSOturum,
    KonuTakip,
    HedefTuru,
    Hedef,
    CalismaPlanı,
    CalismaOturumu,
    Hatirlatici
)

@admin.register(YKSOturum)
class YKSOturumAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kod', 'yil', 'sinav_tarihi', 'durum')
    list_filter = ('durum', 'yil')
    search_fields = ('ad', 'kod')

@admin.register(KonuTakip)
class KonuTakipAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'konu', 'tamamlandi', 'tamamlanma_tarihi')
    list_filter = ('tamamlandi', 'tamamlanma_tarihi')
    search_fields = ('kullanici__username', 'konu__ad')
    date_hierarchy = 'tamamlanma_tarihi'
    raw_id_fields = ('kullanici', 'konu')

@admin.register(HedefTuru)
class HedefTuruAdmin(admin.ModelAdmin):
    list_display = ('ad', 'aciklama')
    search_fields = ('ad',)

@admin.register(Hedef)
class HedefAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kullanici', 'tur', 'hedef_durum', 'oncelik', 'baslangic_tarihi', 'bitis_tarihi', 'tamamlanma_orani')
    list_filter = ('hedef_durum__ad', 'oncelik', 'tur', 'baslangic_tarihi')
    search_fields = ('baslik', 'kullanici__username')
    date_hierarchy = 'baslangic_tarihi'

@admin.register(CalismaPlanı)
class CalismaPlanıAdmin(admin.ModelAdmin):
    list_display = ('kullanici', 'tarih', 'toplam_calisma_suresi')
    list_filter = ('tarih',)
    search_fields = ('kullanici__username',)
    date_hierarchy = 'tarih'

@admin.register(CalismaOturumu)
class CalismaOturumuAdmin(admin.ModelAdmin):
    list_display = ('plan', 'ders', 'baslangic_saati', 'bitis_saati', 'sure', 'tamamlandi')
    list_filter = ('tamamlandi', 'baslangic_saati')
    search_fields = ('ders__ad', 'konu__ad')

@admin.register(Hatirlatici)
class HatirlaticiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kullanici', 'hatirlatma_tarihi', 'aktif')
    list_filter = ('aktif', 'hatirlatma_tarihi')
    search_fields = ('baslik', 'kullanici__username')
    date_hierarchy = 'hatirlatma_tarihi'
