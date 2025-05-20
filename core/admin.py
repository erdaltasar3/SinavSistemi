from django.contrib import admin
from .models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu
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
