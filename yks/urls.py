from django.urls import path
from . import views

app_name = 'yks'

urlpatterns = [
    path('', views.index, name='index'),
    path('oturum/<str:oturum_kodu>/', views.oturum_dersleri, name='oturum_dersleri'),
    
    # Konu Takip URL'leri
    path('konu-takip/', views.konu_takip_sinav_secim, name='konu_takip_sinav_secim'),
    path('konu-takip/dersler/<str:sinav_kodu>/', views.konu_takip_dersler, name='konu_takip_dersler'),
    path('konu-takip/konular/<int:ders_id>/', views.konu_takip_konular, name='konu_takip_konular'),
    path('konu-takip/konu-durum-guncelle/', views.konu_durum_guncelle, name='konu_durum_guncelle'),
    
    # API için URL'ler
    path('api/ders/<int:ders_id>/konular/', views.ders_konulari_api, name='ders_konulari_api'),
    
    # Hedef Belirleme ve Takip URL'leri
    path('hedefler/', views.hedef_listesi, name='hedef_listesi'),
    path('hedefler/ekle/', views.hedef_ekle, name='hedef_ekle'),
    path('hedefler/duzenle/<int:hedef_id>/', views.hedef_duzenle, name='hedef_duzenle'),
    path('hedefler/sil/<int:hedef_id>/', views.hedef_sil, name='hedef_sil'),
    path('hedefler/durum-guncelle/<int:hedef_id>/', views.hedef_durum_guncelle, name='hedef_durum_guncelle'),
    path('hedef-turu-sec/', views.hedef_turu_sec, name='hedef_turu_sec'),
    path('hedefler/ekle/soru-cozumu/', views.soru_cozum_hedef_ekle, name='soru_cozum_hedef_ekle'),
    path('hedefler/ekle/konu-takip/', views.konu_takip_hedef_ekle, name='konu_takip_hedef_ekle'),
    path('hedefler/ilerleme/<int:hedef_id>/', views.hedef_ilerleme_kaydet, name='hedef_ilerleme_kaydet'),
    path('hedefler/ilerleme/soru/<int:hedef_id>/', views.soru_cozum_ilerleme, name='soru_cozum_ilerleme'),
    path('hedefler/ilerleme/konu/<int:hedef_id>/', views.konu_takip_ilerleme, name='konu_takip_ilerleme'),
    
    # Çalışma Planı URL'leri
    path('calisma-plani/', views.calisma_plani_listesi, name='calisma_plani_listesi'),
    path('calisma-plani/ekle/', views.calisma_plani_ekle, name='calisma_plani_ekle'),
    path('calisma-plani/<int:plan_id>/', views.calisma_plani_detay, name='calisma_plani_detay'),
    path('calisma-plani/oturum-tamamlandi-yap/<int:oturum_id>/', views.oturum_tamamlandi_yap, name='calisma_oturum_tamamlandi_yap'),
    path('calisma-plani/oturum-sil/<int:oturum_id>/', views.oturum_sil, name='calisma_oturum_sil'),
    path('calisma-plani/oturum-geri-al/<int:oturum_id>/', views.calisma_oturum_geri_al, name='calisma_oturum_geri_al'),
    
    # Hatırlatıcılar URL'leri
    path('hatirlaticilar/', views.hatirlatici_listesi, name='hatirlatici_listesi'),
    path('hatirlaticilar/ekle/', views.hatirlatici_ekle, name='hatirlatici_ekle'),
    path('hatirlaticilar/duzenle/<int:hatirlatici_id>/', views.hatirlatici_duzenle, name='hatirlatici_duzenle'),
    path('hatirlaticilar/sil/<int:hatirlatici_id>/', views.hatirlatici_sil, name='hatirlatici_sil'),
    path('hatirlaticilar/durum-guncelle/<int:hatirlatici_id>/', views.hatirlatici_durum_guncelle, name='hatirlatici_durum_guncelle'),
    
    # AJAX için URL'ler
    path('api/dersler/', views.dersler_json, name='dersler_json'),
    path('api/dersler/<int:ders_id>/konular/', views.konular_json, name='konular_json'),
] 