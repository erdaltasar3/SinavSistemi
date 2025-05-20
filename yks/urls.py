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
    
    # Çalışma Planı URL'leri
    path('calisma-plani/', views.calisma_plani_listesi, name='calisma_plani_listesi'),
    path('calisma-plani/ekle/', views.calisma_plani_ekle, name='calisma_plani_ekle'),
    path('calisma-plani/<int:plan_id>/', views.calisma_plani_detay, name='calisma_plani_detay'),
    path('calisma-plani/oturum-sil/<int:oturum_id>/', views.oturum_sil, name='oturum_sil'),
    
    # Görevler URL'leri
    path('gorevler/', views.gorev_listesi, name='gorev_listesi'),
    path('gorevler/ekle/', views.gorev_ekle, name='gorev_ekle'),
    path('gorevler/duzenle/<int:gorev_id>/', views.gorev_duzenle, name='gorev_duzenle'),
    path('gorevler/sil/<int:gorev_id>/', views.gorev_sil, name='gorev_sil'),
    path('gorevler/durum-guncelle/<int:gorev_id>/', views.gorev_durum_guncelle, name='gorev_durum_guncelle'),
    
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