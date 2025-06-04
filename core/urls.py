from django.urls import path
from . import views
from .views import profile_view, send_verification_email, verify_email_code

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
    
    # E-posta doğrulama URL'leri
    path('send-verification-email/', send_verification_email, name='send_verification_email'),
    path('verify-email-code/', verify_email_code, name='verify_email_code'),

    # Devre dışı bırakılan URL'ler
    # Hedefler, Planlar, Hatırlatıcılar ve Yapılacaklar için URL'ler
    # artık kullanılmıyor
    path('profile/', profile_view, name='profile'),
] 