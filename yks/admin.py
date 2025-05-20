from django.contrib import admin
from .models import YKSOturum, KonuTakip

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
