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
] 