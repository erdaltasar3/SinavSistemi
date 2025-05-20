from django.contrib import admin
from .models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu,
    CalismaHedefi, CalismaPlani, Hatirlatici, YapilacakListesi
)

@admin.register(SinavTurleri)
class SinavTurleriAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kod', 'aktif')
    list_filter = ('aktif',)
    search_fields = ('ad', 'kod')

@admin.register(SinavAltTur)
class SinavAltTurAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kod', 'sinav_turu', 'aktif')
    list_filter = ('aktif', 'sinav_turu')
    search_fields = ('ad', 'kod')

@admin.register(Ders)
class DersAdmin(admin.ModelAdmin):
    list_display = ('ad', 'kod', 'alt_tur', 'aktif')
    list_filter = ('aktif', 'alt_tur')
    search_fields = ('ad', 'kod')

admin.site.register(Unite)
admin.site.register(Konu)

@admin.register(CalismaHedefi)
class CalismaHedefiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kullanici', 'periyot', 'baslangic_tarihi', 'bitis_tarihi', 'durum')
    list_filter = ('durum', 'periyot')
    search_fields = ('baslik', 'kullanici__username')
    date_hierarchy = 'baslangic_tarihi'

@admin.register(CalismaPlani)
class CalismaPlaniAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'hedef', 'plan_turu', 'planlanan_tarih', 'planlanan_sure', 'gerceklesen_sure', 'durum')
    list_filter = ('durum', 'plan_turu')
    search_fields = ('baslik', 'hedef__baslik', 'hedef__kullanici__username')
    date_hierarchy = 'planlanan_tarih'

@admin.register(Hatirlatici)
class HatirlaticiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kullanici', 'tarih', 'saat', 'oncelik', 'durum')
    list_filter = ('durum', 'oncelik')
    search_fields = ('baslik', 'kullanici__username')
    date_hierarchy = 'tarih'

@admin.register(YapilacakListesi)
class YapilacakListesiAdmin(admin.ModelAdmin):
    list_display = ('baslik', 'kullanici', 'son_tarih', 'oncelik', 'durum')
    list_filter = ('durum', 'oncelik')
    search_fields = ('baslik', 'kullanici__username')
    date_hierarchy = 'son_tarih'
