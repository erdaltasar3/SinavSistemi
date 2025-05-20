from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Case, When, IntegerField, Q, Sum, F, Avg, Exists, OuterRef
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from core.models import (
    SinavAltTur, Ders, Unite, Konu, SinavTurleri
)
from .models import YKSOturum, KonuTakip
from datetime import date, timedelta

def index(request):
    """YKS ana sayfa görünümü"""
    # YKS oturumlarını getir
    oturumlar = YKSOturum.objects.filter(durum=YKSOturum.DURUM_BEKLIYOR).order_by('sinav_tarihi')
    
    context = {
        'oturumlar': oturumlar,
    }
    
    return render(request, 'yks/index.html', context)

def oturum_dersleri(request, oturum_kodu):
    """YKS oturumuna ait dersleri gösterir"""
    oturum = get_object_or_404(YKSOturum, kod=oturum_kodu)
    # SinavAltTur üzerinden dersleri getir
    sinav_alt_tur = get_object_or_404(SinavAltTur, kod=oturum_kodu)
    # Doğru filtreleme: Ders modelindeki alt_tur ilişkisini kullan
    dersler = Ders.objects.filter(alt_tur=sinav_alt_tur)
    
    context = {
        'oturum': oturum,
        'alt_tur': sinav_alt_tur,
        'dersler': dersler,
    }
    
    return render(request, 'yks/oturum_dersleri.html', context)

# Konu Takip Görünümleri
def konu_takip_sinav_secim(request):
    """Konu takibi için sınav seçim sayfasını gösterir"""
    # Tüm sınav alt türlerini getir ve sonra filtrele
    alt_turler = SinavAltTur.objects.all().order_by('ad')
    
    # Sorgu sonuçlarını kontrol için
    print(f"Toplam alt tür sayısı: {alt_turler.count()}")
    for alt_tur in alt_turler:
        print(f"Alt tür: {alt_tur.ad} (Kod: {alt_tur.kod})")
    
    context = {
        'alt_turler': alt_turler,
    }
    
    return render(request, 'yks/konu_takip/sinav_secim.html', context)

@login_required
def konu_takip_dersler(request, sinav_kodu):
    """Seçilen sınav türüne ait dersleri listeler"""
    try:
        # Önce veritabanından alt türü bulmaya çalış
        alt_tur = get_object_or_404(SinavAltTur, kod=sinav_kodu)
    except:
        # Veritabanında yoksa manuel bir alt_tur nesnesi oluştur
        from django.db import models
        
        # Alt tür koduna göre isim belirle
        if sinav_kodu == 'TYT':
            alt_tur_adi = 'Temel Yeterlilik Testi'
        elif sinav_kodu == 'AYT':
            alt_tur_adi = 'Alan Yeterlilik Testi'
        elif sinav_kodu == 'YDT':
            alt_tur_adi = 'Yabancı Dil Testi' 
        else:
            alt_tur_adi = f'Bilinmeyen Alt Tür: {sinav_kodu}'
        
        # Geçici bir nesne oluştur
        class TempAltTur:
            def __init__(self, kod, ad):
                self.kod = kod
                self.ad = ad
        
        alt_tur = TempAltTur(sinav_kodu, alt_tur_adi)
        
        # Logla
        print(f"UYARI: {sinav_kodu} alt türü veritabanında bulunamadı, geçici nesne oluşturuldu")
    
    # Seçilen sınav türüne ait dersleri al (eğer alt_tur gerçek bir veritabanı nesnesiyse)
    try:
        dersler = Ders.objects.filter(alt_tur=alt_tur).order_by('ad')
    except:
        # Alt tür geçici ise boş queryset kullan
        print(f"UYARI: {sinav_kodu} için dersler sorgulanamadı")
        dersler = Ders.objects.none()  
    
    # Her ders için ünite ve konu sayılarını hesapla
    dersler_data = []
    
    for ders in dersler:
        # Derse ait tüm üniteleri al
        uniteler = Unite.objects.filter(ders=ders)
        
        # Tüm konuları al ve tamamlanan konu sayısını hesapla
        tum_konular = Konu.objects.filter(unite__in=uniteler)
        toplam_konu_sayisi = tum_konular.count()
        
        # Kullanıcı için tamamlanan konuları bul
        if request.user.is_authenticated:
            tamamlanan_konu_sayisi = KonuTakip.objects.filter(
                kullanici=request.user,
                konu__unite__in=uniteler,
                tamamlandi=True
            ).count()
        else:
            tamamlanan_konu_sayisi = 0
        
        # İlerleme yüzdesini hesapla
        ilerleme_yuzdesi = 0
        if toplam_konu_sayisi > 0:
            ilerleme_yuzdesi = (tamamlanan_konu_sayisi / toplam_konu_sayisi) * 100
        
        dersler_data.append({
            'ders': ders,
            'toplam_konu': toplam_konu_sayisi,
            'tamamlanan_konu': tamamlanan_konu_sayisi,
            'ilerleme_yuzdesi': ilerleme_yuzdesi
        })
    
    # Tek bir alt_tur altında tüm dersleri grupla
    alt_tur_dersler = [
        {
            'alt_tur': alt_tur,
            'dersler': dersler_data
        }
    ] if dersler_data else []
    
    context = {
        'sinav_kodu': sinav_kodu,
        'alt_tur_dersler': alt_tur_dersler
    }
    
    return render(request, 'yks/konu_takip/dersler.html', context)

@login_required
def konu_takip_konular(request, ders_id):
    """Seçilen derse ait konuları listeler"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders).order_by('sira_no')
    
    # Her ünite için konuları ve ilerleme durumunu hazırla
    unite_verileri = []
    for unite in uniteler:
        konular = Konu.objects.filter(unite=unite).order_by('sira_no')
        
        # Bu ünitedeki toplam konu sayısı
        toplam_konu_sayisi = konular.count()
        
        # Bu ünitedeki tamamlanan konu sayısı (kullanıcıya göre)
        tamamlanan_konu_sayisi = KonuTakip.objects.filter(
            kullanici=request.user,
            konu__unite=unite,
            tamamlandi=True
        ).count()
        
        # Her konu için tamamlanma durumunu belirle
        konu_verileri = []
        for konu in konular:
            # Konunun tamamlanma durumunu kontrol et
            tamamlandi = KonuTakip.objects.filter(
                kullanici=request.user,
                konu=konu,
                tamamlandi=True
            ).exists()
            
            konu_verileri.append({
                'id': konu.id,
                'ad': konu.ad,
                'tamamlandi': tamamlandi
            })
        
        # Tamamlanma yüzdesi
        tamamlanma_yuzdesi = 0
        if toplam_konu_sayisi > 0:
            tamamlanma_yuzdesi = (tamamlanan_konu_sayisi / toplam_konu_sayisi) * 100
        
        unite_verileri.append({
            'unite': unite,
            'konular': konu_verileri,
            'toplam_konu': toplam_konu_sayisi,
            'tamamlanan_konu': tamamlanan_konu_sayisi,
            'tamamlanma_yuzdesi': tamamlanma_yuzdesi
        })
    
    # Genel toplam ve tamamlanan konu sayılarını hesapla
    toplam_konular = 0
    toplam_tamamlanan = 0
    
    for unite_veri in unite_verileri:
        toplam_konular += unite_veri['toplam_konu']
        toplam_tamamlanan += unite_veri['tamamlanan_konu']
    
    # Genel tamamlanma yüzdesi
    genel_yuzde = 0
    if toplam_konular > 0:
        genel_yuzde = (toplam_tamamlanan / toplam_konular) * 100
    
    context = {
        'ders': ders,
        'uniteler': unite_verileri,
        'toplam_konular': toplam_konular,
        'toplam_tamamlanan': toplam_tamamlanan,
        'genel_yuzde': genel_yuzde
    }
    
    return render(request, 'yks/konu_takip/konular.html', context)

@login_required
@csrf_exempt
def konu_durum_guncelle(request):
    """AJAX ile konu durumunu güncelleme"""
    if request.method == "POST" and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            konu_id = request.POST.get('konu_id')
            tamamlandi = request.POST.get('tamamlandi') == 'true'
            
            # Konu var mı kontrol et
            konu = get_object_or_404(Konu, id=konu_id)
            
            if tamamlandi:
                # KonuTakip kaydını bul veya oluştur
                konu_takip, created = KonuTakip.objects.get_or_create(
                    kullanici=request.user,
                    konu=konu,
                    defaults={'tamamlandi': True}
                )
                
                # Eğer kayıt zaten varsa, durumu tamamlandı olarak güncelle
                if not created and not konu_takip.tamamlandi:
                    konu_takip.tamamlandi = True
                    konu_takip.save()
            else:
                # Tamamlanmadı olarak işaretlendiyse, kaydı sil
                KonuTakip.objects.filter(
                    kullanici=request.user,
                    konu=konu
                ).delete()
            
            return JsonResponse({
                'success': True, 
                'konu_id': konu_id,
                'tamamlandi': tamamlandi
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Geçersiz istek'})

# API Görünümleri
@login_required
def ders_konulari_api(request, ders_id):
    """Belirli bir derse ait konuları JSON formatında döndürür"""
    konular = Konu.objects.filter(unite__ders_id=ders_id).values('id', 'ad')
    return JsonResponse(list(konular), safe=False)
