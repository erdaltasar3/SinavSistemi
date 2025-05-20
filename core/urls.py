from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('giris/', views.giris_view, name='giris'),
    path('kayit/', views.kayit_view, name='kayit'),
    path('cikis/', views.cikis_view, name='cikis'),
    path('hata/403/', views.hata_403, name='hata_403'),
    path('hata/404/', views.hata_404, name='hata_404'),
    path('hata/500/', views.hata_500, name='hata_500'),
    
    # Yetkili paneli
    path('yetkili/', views.yetkili_panel, name='yetkili_panel'),
    path('yetkili/oturumlar/', views.oturumlar_view, name='oturumlar'),
    path('yetkili/oturumlar/ekle/', views.oturum_ekle, name='oturum_ekle'),
    path('yetkili/oturumlar/<str:sinav_kodu>/', views.oturum_detay, name='oturum_detay'),
    path('yetkili/oturumlar/<str:sinav_kodu>/<str:alt_tur_kodu>/', views.oturum_detay, name='oturum_alt_tur_detay'),
    
    # Ders düzenleme
    path('yetkili/ders/<int:ders_id>/duzenle/', views.ders_duzenle, name='ders_duzenle'),
    path('yetkili/ders/<int:ders_id>/sil/', views.ders_sil, name='ders_sil'),
    path('yetkili/ders/<int:ders_id>/uniteler-son-sira/', views.ders_uniteler_son_sira_api, name='ders_uniteler_son_sira_api'),
    
    # Ünite işlemleri
    path('yetkili/unite/ekle/', views.unite_ekle, name='unite_ekle'),
    path('yetkili/unite/<int:unite_id>/duzenle/', views.unite_duzenle, name='unite_duzenle'),
    path('yetkili/unite/<int:unite_id>/sil/', views.unite_sil, name='unite_sil'),
    path('yetkili/unite/<int:unite_id>/konular-son-sira/', views.unite_konular_son_sira_api, name='unite_konular_son_sira_api'),
    
    # Konu işlemleri
    path('yetkili/konu/ekle/', views.konu_ekle, name='konu_ekle'),
    path('yetkili/konu/<int:konu_id>/duzenle/', views.konu_duzenle, name='konu_duzenle'),
    path('yetkili/konu/<int:konu_id>/sil/', views.konu_sil, name='konu_sil'),
    
    # API endpoint'leri
    path('api/sinav/<int:sinav_turu_id>/alt-turler/', views.sinav_alt_turler_api, name='sinav_alt_turler_api'),
    path('api/ders/ekle/', views.ders_ekle, name='ders_ekle'),
    
    # Hedef Belirleme ve Takip URL'leri
    path('hedefler/', views.hedef_listesi, name='hedef_listesi'),
    path('hedefler/ekle/', views.hedef_ekle, name='hedef_ekle'),
    path('hedefler/<int:hedef_id>/', views.hedef_detay, name='hedef_detay'),
    path('hedefler/<int:hedef_id>/duzenle/', views.hedef_duzenle, name='hedef_duzenle'),
    path('hedefler/<int:hedef_id>/sil/', views.hedef_sil, name='hedef_sil'),
    
    # Çalışma planı URL'leri
    path('hedefler/<int:hedef_id>/plan/ekle/', views.plan_ekle, name='plan_ekle'),
    path('plan/<int:plan_id>/', views.plan_detay, name='plan_detay'),
    path('plan/<int:plan_id>/duzenle/', views.plan_duzenle, name='plan_duzenle'),
    path('plan/<int:plan_id>/sil/', views.plan_sil, name='plan_sil'),
    path('plan/<int:plan_id>/tamamla/', views.plan_tamamla, name='plan_tamamla'),
    
    # Hatırlatıcı URL'leri
    path('hatirlaticilar/', views.hatirlatici_listesi, name='hatirlatici_listesi'),
    path('hatirlaticilar/ekle/', views.hatirlatici_ekle, name='hatirlatici_ekle'),
    path('hatirlaticilar/<int:hatirlatici_id>/', views.hatirlatici_detay, name='hatirlatici_detay'),
    path('hatirlaticilar/<int:hatirlatici_id>/duzenle/', views.hatirlatici_duzenle, name='hatirlatici_duzenle'),
    path('hatirlaticilar/<int:hatirlatici_id>/sil/', views.hatirlatici_sil, name='hatirlatici_sil'),
    path('hatirlaticilar/<int:hatirlatici_id>/tamamla/', views.hatirlatici_tamamla, name='hatirlatici_tamamla'),
    
    # Yapılacaklar listesi URL'leri
    path('yapilacaklar/', views.yapilacak_listesi, name='yapilacak_listesi'),
    path('yapilacaklar/ekle/', views.yapilacak_ekle, name='yapilacak_ekle'),
    path('yapilacaklar/<int:yapilacak_id>/', views.yapilacak_detay, name='yapilacak_detay'),
    path('yapilacaklar/<int:yapilacak_id>/duzenle/', views.yapilacak_duzenle, name='yapilacak_duzenle'),
    path('yapilacaklar/<int:yapilacak_id>/sil/', views.yapilacak_sil, name='yapilacak_sil'),
    path('yapilacaklar/<int:yapilacak_id>/tamamla/', views.yapilacak_tamamla, name='yapilacak_tamamla'),
] 