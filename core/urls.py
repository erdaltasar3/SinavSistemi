from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('giris/', views.giris_view, name='giris'),
    path('kayit/', views.kayit_view, name='kayit'),
    path('cikis/', views.cikis_view, name='cikis'),
    path('yetkili/', views.yetkili_panel, name='yetkili_panel'),
    path('yetkili/oturum-ekle/', views.oturum_ekle, name='oturum_ekle'),
    path('yetkili/oturumlar/', views.oturumlar_view, name='oturumlar'),
    path('yetkili/oturumlar/<str:sinav_kodu>/', views.oturum_detay, name='oturum_detay'),
    path('yetkili/oturumlar/<str:sinav_kodu>/<str:alt_tur_kodu>/', views.oturum_detay, name='oturum_alt_tur_detay'),
    path('api/sinav-turleri/<int:sinav_turu_id>/alt-turler/', views.sinav_alt_turler_api, name='sinav_alt_turler_api'),
    path('api/ders/ekle/', views.ders_ekle, name='ders_ekle'),
] 