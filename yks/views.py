from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, Http404
from django.utils import timezone
from django.db.models import Count, Case, When, IntegerField, Q, Sum, F, Avg, Exists, OuterRef, BooleanField, Value
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from core.models import (
    SinavAltTur, Ders, Unite, Konu, SinavTurleri, UserProfile
)
from .models import (
    YKSOturum, 
    KonuTakip, 
    Hedef, 
    HedefTuru, 
    CalismaPlanı, 
    CalismaOturumu, 
    Hatirlatici,
    SoruCozumHedefi,
    KonuTakipHedefi,
    KonuTakipHedefKonu,
    HedefDurum,
    DenemeSinavSonucu,
    DenemeSinavDersSonucu
)
from .forms import (
    HedefForm,
    HedefDuzenleForm,
    CalismaPlanForm,
    CalismaOturumuForm,
    HatirlaticiForm,
    UserProfileForm
)
from datetime import date, timedelta
from django.contrib.auth import update_session_auth_hash
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
import json
import calendar
import os


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
def ders_konulari_api(request):
    """AJAX için dersleri JSON formatında döndürür"""
    dersler = Ders.objects.filter(aktif=True).order_by('alt_tur', 'ad')
    
    data = [
        {
            'id': ders.id,
            'ad': ders.ad,
            'kod': ders.kod,
            'alt_tur': ders.alt_tur.ad if ders.alt_tur else None
        }
        for ders in dersler
    ]
    
    return JsonResponse(data, safe=False)

@login_required
def konular_json(request, ders_id):
    """AJAX için belirli bir derse ait konuları JSON formatında döndürür"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders).order_by('sira_no')
    
    data = []
    
    for unite in uniteler:
        konular = Konu.objects.filter(unite=unite).order_by('sira_no')
        
        for konu in konular:
            data.append({
                'id': konu.id,
                'ad': konu.ad,
                'unite': unite.ad
            })
    
    return JsonResponse(data, safe=False)

# Hedef Belirleme ve Takip Görünümleri
@login_required
def hedef_listesi(request):
    """
    Kullanıcının hedeflerini sekme (aktif, tamamlanan, tamamlanmayan) ve tür (Günlük, Haftalık, Özel) filtrelerine göre listeler
    """
    # Hedeflerin durumunu güncelle: Bitiş tarihi geçmiş hedefleri otomatik tamamlandı/tamamlanmadı yap
    bugun = timezone.now().date()
    gecmis_hedefler = Hedef.objects.filter(
        kullanici=request.user,
        bitis_tarihi__lt=bugun,
        hedef_durum__id=1  # Sadece Aktif hedefleri güncelle
    )
    
    for hedef in gecmis_hedefler:
        # Hedefin tamamlanma oranını kontrol et
        if hedef.tamamlanma_orani == 100:
            # %100 tamamlandıysa durumunu "Tamamlandı" yap (ID=2)
            hedef.hedef_durum_id = 2
            hedef.save()
        else:
            # %100 tamamlanmadıysa durumunu "Tamamlanmadı" yap (ID=3)
            hedef.hedef_durum_id = 3
            hedef.save()
    
    # Parametreleri al
    sekme = request.GET.get('sekme', 'aktif')
    tur = request.GET.get('tur', 'Günlük')

    # Temel queryset
    hedefler = Hedef.objects.filter(kullanici=request.user)
    
    # İstatistikler için filtrelenmiş sorgu başlat (sadece aktif filtrelere göre)
    filtrelenmis_hedefler = hedefler
    
    # Sekmeye göre filtrele (hem görüntüleme hem de istatistikler için)
    if sekme == 'aktif':
        # Aktif hedefler: Durumu AKTIF olanlar (ID=1)
        hedefler = hedefler.filter(hedef_durum__id=1)
        filtrelenmis_hedefler = filtrelenmis_hedefler.filter(hedef_durum__id=1)
    elif sekme == 'tamamlanan':
        # Tamamlanan hedefler: Durumu TAMAMLANDI olanlar (ID=2)
        hedefler = hedefler.filter(hedef_durum__id=2)
        filtrelenmis_hedefler = filtrelenmis_hedefler.filter(hedef_durum__id=2)
    elif sekme == 'tamamlanmayan':
        # Tamamlanmayan hedefler: Durumu TAMAMLANMADI olanlar (ID=3)
        hedefler = hedefler.filter(hedef_durum__id=3)
        filtrelenmis_hedefler = filtrelenmis_hedefler.filter(hedef_durum__id=3)
    else:
        # Varsayılan olarak aktif hedefler gösterilsin (ID=1)
        hedefler = hedefler.filter(hedef_durum__id=1)
        filtrelenmis_hedefler = filtrelenmis_hedefler.filter(hedef_durum__id=1)

    # Tür filtresi uygula (hem görüntüleme hem de istatistikler için)
    if tur != 'Hepsi': 
        hedefler = hedefler.filter(tur__ad=tur)
        filtrelenmis_hedefler = filtrelenmis_hedefler.filter(tur__ad=tur)

    # Sıralama
    hedefler = hedefler.order_by('bitis_tarihi', '-oncelik') 

    # Her hedef için detay bilgilerini al
    hedef_listesi = []
    for hedef in hedefler:
        hedef_data = {
            'hedef': hedef,
            'tip': None,
            'ilerleme': 0
        }

        # İlerleme oranını hesapla
        try:
            soru_cozum = hedef.soru_cozum_detay
            hedef_data['tip'] = 'soru_cozum'
            hedef_data['ilerleme'] = soru_cozum.ilerleme_orani()
        except SoruCozumHedefi.DoesNotExist:
            pass

        try:
            konu_takip = hedef.konu_takip_detay
            hedef_data['tip'] = 'konu_takip'
            hedef_data['ilerleme'] = konu_takip.ilerleme_orani()
        except KonuTakipHedefi.DoesNotExist:
            pass

        # Genel Hedef tamamlanma oranını kullan, eğer alt detay ilerlemesi 0 ise
        if hedef_data['tip'] is None and hedef.tamamlanma_orani > 0:
             hedef_data['ilerleme'] = hedef.tamamlanma_orani
        # Alt detay ilerlemesi 0 ise ve genel oran > 0 ise genel oranı kullan
        elif hedef_data['ilerleme'] == 0 and hedef.tamamlanma_orani > 0:
             hedef_data['ilerleme'] = hedef.tamamlanma_orani

        hedef_listesi.append(hedef_data)

    # İstatistikler (Filtrelere göre hesaplama)
    toplam_hedef = filtrelenmis_hedefler.count()
    tamamlanan_sayisi = filtrelenmis_hedefler.filter(tamamlanma_orani=100).count()
    tamamlanma_yuzdesi = (tamamlanan_sayisi / toplam_hedef) * 100 if toplam_hedef > 0 else 0

    context = {
        'hedefler': hedef_listesi,
        'sekme': sekme,
        'tur': tur,
        'toplam_hedef': toplam_hedef,
        'tamamlanan_sayisi': tamamlanan_sayisi,
        'tamamlanma_yuzdesi': tamamlanma_yuzdesi,
    }
    return render(request, 'yks/hedef_belirleme/hedef_listesi.html', context)

@login_required
def hedef_ekle(request):
    """Yeni hedef ekleme görünümü"""
    if request.method == 'POST':
        form = HedefForm(request.POST)
        if form.is_valid():
            hedef = form.save(commit=False)
            hedef.kullanici = request.user
            hedef.save()
            messages.success(request, 'Hedef başarıyla eklendi.')
            return redirect('yks:hedef_listesi')
    else:
        form = HedefForm()
    
    # Hedef türlerini kontrol et, yoksa oluştur
    tur_sayisi = HedefTuru.objects.count()
    if tur_sayisi == 0:
        # Varsayılan türleri oluştur
        HedefTuru.objects.create(ad=HedefTuru.GUNLUK, aciklama="Günlük hedefler")
        HedefTuru.objects.create(ad=HedefTuru.HAFTALIK, aciklama="Haftalık hedefler")
        HedefTuru.objects.create(ad=HedefTuru.AYLIK, aciklama="Aylık hedefler")
        HedefTuru.objects.create(ad=HedefTuru.OZEL, aciklama="Özel hedefler")
    
    context = {
        'form': form,
    }
    
    return render(request, 'yks/hedef_belirleme/hedef_ekle.html', context)

@login_required
def hedef_duzenle(request, hedef_id):
    """
    Hedef düzenleme görünümü ve POST işlemi. Hem genel hedefi hem de alt detayları (soru/konu) günceller.
    """
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)

    if request.method == 'POST':
        # Formdan gelen genel hedef verilerini işle
        form = HedefDuzenleForm(request.POST, instance=hedef)
        if form.is_valid():
            form.save()

            # Hedef tipine göre alt detayları güncelle
            try:
                soru_cozum = hedef.soru_cozum_detay
                # Soru çözümü hedefi güncelleme
                cozulmus_soru = int(request.POST.get('cozulmus_soru', 0))
                soru_cozum.cozulmus_soru = cozulmus_soru
                soru_cozum.save()

                # Hedef durumunu ilerlemeye göre otomatik güncelle
                if soru_cozum.ilerleme_orani() >= 100:
                    hedef.hedef_durum = HedefDurum.objects.get(ad='Tamamlandı')
                    hedef.tamamlanma_orani = 100
                    hedef.guncelleme_tarihi = timezone.now()
                else:
                    # Eğer tamamlanma oranı %100 değilse durumu AKTIF yap (IPTAL veya diğer durumları bozmamak için dikkatli olmak lazım)
                    # Sadece AKTIF durumdan %100 olmayan bir orana düşerse AKTIF kalsın
                    if hedef.hedef_durum.ad == 'Tamamlandı' and soru_cozum.ilerleme_orani() < 100:
                         # Tamamlanmış bir hedef tekrar düzenlenip ilerlemesi düşürülürse durumu Aktif'e çek
                         hedef.hedef_durum = HedefDurum.objects.get(ad='Aktif')
                         hedef.tamamlanma_orani = soru_cozum.ilerleme_orani()
                    elif hedef.hedef_durum.ad == 'Aktif':
                         hedef.tamamlanma_orani = soru_cozum.ilerleme_orani()

                hedef.save() # Genel hedefi kaydet

                messages.success(request, 'Soru çözümü hedefi başarıyla güncellendi.')

            except SoruCozumHedefi.DoesNotExist:
                 pass # Soru çözümü hedefi yoksa geç

            try:
                konu_takip = hedef.konu_takip_detay
                # Konu takibi hedefi güncelleme
                # Konu Takip Hedef Konu objelerini güncelle
                tamamlanan_konular_ids = request.POST.getlist('konular') # Formdan gelen tamamlanan konu ID'leri

                # Hedefe bağlı tüm KonuTakipHedefKonu objelerini al
                all_konu_hedef_konular = konu_takip.konular.all()

                # Gelen ID listesindeki konuları tamamlandı olarak işaretle
                for konu_hedef_konu in all_konu_hedef_konular:
                    if str(konu_hedef_konu.konu.id) in tamamlanan_konular_ids:
                        konu_hedef_konu.tamamlandi = True
                    else:
                        konu_hedef_konu.tamamlandi = False
                    konu_hedef_konu.save()

                # Hedef durumunu ilerlemeye göre otomatik güncelle
                if konu_takip.ilerleme_orani() >= 100:
                    hedef.hedef_durum = HedefDurum.objects.get(ad='Tamamlandı')
                    hedef.tamamlanma_orani = 100
                    hedef.guncelleme_tarihi = timezone.now()
                else:
                     # Eğer tamamlanma oranı %100 değilse durumu AKTIF yap
                     if hedef.hedef_durum.ad == 'Tamamlandı' and konu_takip.ilerleme_orani() < 100:
                         # Tamamlanmış bir hedef tekrar düzenlenip ilerlemesi düşürülürse durumu Aktif'e çek
                         hedef.hedef_durum = HedefDurum.objects.get(ad='Aktif')
                         hedef.tamamlanma_orani = konu_takip.ilerleme_orani()
                     elif hedef.hedef_durum.ad == 'Aktif':
                         hedef.tamamlanma_orani = konu_takip.ilerleme_orani()

                hedef.save() # Genel hedefi kaydet

                messages.success(request, 'Konu takibi hedefi başarıyla güncellendi.')

            except KonuTakipHedefi.DoesNotExist:
                pass # Konu takibi hedefi yoksa geç


            return redirect('yks:hedef_listesi') # Güncelleme sonrası hedef listesine yönlendir
        else:
            # Form geçerli değilse aynı sayfayı hata mesajlarıyla göster
            messages.error(request, 'Lütfen form hatalarını düzeltin.')

    else:
        # GET isteği veya form geçerli değilse formu oluştur
        form = HedefDuzenleForm(instance=hedef)

    # Hedef tipini ve ilgili verileri belirle (template için)
    hedef.tip = None
    try:
        hedef.soru_cozum_detay
        hedef.tip = 'soru_cozum'
        hedef.ilerleme = hedef.soru_cozum_detay.ilerleme_orani()
        hedef.cozulmus_soru = hedef.soru_cozum_detay.cozulmus_soru
        hedef.toplam_soru = hedef.soru_cozum_detay.toplam_soru
    except SoruCozumHedefi.DoesNotExist:
        pass

    try:
        hedef.konu_takip_detay
        hedef.tip = 'konu_takip'
        hedef.ilerleme = hedef.konu_takip_detay.ilerleme_orani()
        hedef.konular = hedef.konu_takip_detay.konular.all().select_related('konu') # Konuları template'te kullanmak için çek
    except KonuTakipHedefi.DoesNotExist:
        pass

    return render(request, 'yks/hedef_belirleme/hedef_duzenle.html', {
        'form': form, # Düzenleme formu
        'hedef': hedef # Hedef objesi ve eklenen tip/ilerleme bilgileri
    })

@login_required
def hedef_sil(request, hedef_id):
    """Hedef silme görünümü"""
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
    
    if request.method == 'POST':
        hedef.delete()
        messages.success(request, 'Hedef başarıyla silindi.')
        return redirect('yks:hedef_listesi')
    
    context = {
        'hedef': hedef,
    }
    
    return render(request, 'yks/hedef_belirleme/hedef_sil.html', context)

@login_required
def hedef_durum_guncelle(request, hedef_id):
    """AJAX ile hedef durumunu güncelleme"""
    # Bu view'ın CSRF korumasını kapatmak yerine frontend'den CSRF token göndermek daha güvenlidir.
    # @csrf_exempt annotation'ını kaldırıp frontend'den token gönderildiğinden emin olun.
    
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)

        # İsteğin bodysinden 'durum' bilgisini al (frontend JS'den gelecek)
        # Örneğin, JSON: { "durum": "Tamamlandı" }
        import json

        try:
            data = json.loads(request.body)
            yeni_durum_id = data.get('durum_id') # Frontend'den durum ID'si gelecek (örn: 2 for Tamamlandı)

            # Durum ID'sine karşılık gelen HedefDurum objesini bul
            hedef_durum_obj = HedefDurum.objects.get(id=yeni_durum_id)

            # Hedefin durumunu güncelle
            hedef.hedef_durum = hedef_durum_obj

            # Eğer durum 'Tamamlandı' (ID=2) olarak güncelleniyorsa tamamlanma oranını 100 yap
            if yeni_durum_id == 2:
                hedef.tamamlanma_orani = 100
                hedef.guncelleme_tarihi = timezone.now()

            hedef.save()
            return JsonResponse({'success': True, 'message': f'Hedef durumu {hedef_durum_obj.ad} olarak güncellendi.'})
        except HedefDurum.DoesNotExist:
            # HedefDurum objesi bulunamazsa hata döndür
            return JsonResponse({'success': False, 'message': f"Geçersiz hedef durumu ID'si sağlandı."}, status=400)
        except Exception as e:
            # Diğer hatalar için genel hata döndür
            return JsonResponse({'success': False, 'message': f'Durum güncellenirken bir hata oluştu: {str(e)}'}, status=500)

    # Eğer istek metodu POST değilse veya X-Requested-With header'ı yoksa
    return JsonResponse({'success': False, 'message': 'Geçersiz istek metodu veya header.'}, status=405)

# Çalışma Planı Görünümleri
@login_required
def calisma_plani_listesi(request):
    """Kullanıcının çalışma planlarını listeler"""
    
    # Bugünün tarihi
    bugun = timezone.localdate()
    
    # Bugünün planını getir (yoksa None)
    bugunun_plani = CalismaPlanı.objects.filter(
        kullanici=request.user,
        tarih=bugun
    ).first()
    
    # Son 7 günün planlarını getir
    son_planlar = CalismaPlanı.objects.filter(
        kullanici=request.user,
        tarih__gte=bugun - timedelta(days=7),
        tarih__lt=bugun
    ).order_by('-tarih')
    
    # Gelecek planlar
    gelecek_planlar = CalismaPlanı.objects.filter(
        kullanici=request.user,
        tarih__gt=bugun
    ).order_by('tarih')
    
    # Son planlar için tamamlanma bilgilerini hesapla
    for plan in son_planlar:
        plan.toplam_oturum = plan.oturumlar.count()
        if plan.toplam_oturum > 0:
            plan.tamamlanan_oturum = plan.oturumlar.filter(tamamlandi=True).count()
            plan.tamamlanma_yuzdesi = (plan.tamamlanan_oturum / plan.toplam_oturum) * 100
        else:
            plan.tamamlanan_oturum = 0
            plan.tamamlanma_yuzdesi = 0

    # Bugünün planı toplam süresini saate çevir
    bugunun_plani_toplam_saat = 0
    if bugunun_plani and bugunun_plani.toplam_calisma_suresi is not None:
        bugunun_plani_toplam_saat = bugunun_plani.toplam_calisma_suresi / 60

    # Son 7 günün toplam çalışma süresini hesapla
    son_yedi_gun_toplam_sure_dakika = CalismaOturumu.objects.filter(
        plan__kullanici=request.user,
        plan__tarih__gte=bugun - timedelta(days=7),
        plan__tarih__lt=bugun
    ).aggregate(Sum('sure'))['sure__sum'] or 0

    # Toplam süreyi saate çevir
    son_yedi_gun_toplam_saat = son_yedi_gun_toplam_sure_dakika / 60

    # Son 7 günde en çok çalışılan dersleri ve sürelerini hesapla
    yedi_gun_oncesi = bugun - timedelta(days=7)
    en_cok_calisilan_dersler_raw = CalismaOturumu.objects.filter(
        plan__kullanici=request.user,
        plan__tarih__gte=yedi_gun_oncesi,
        plan__tarih__lt=bugun
    ).values('ders__ad').annotate(total_sure=Sum('sure')).order_by('-total_sure')[:3]

    # Toplam 7 günlük süreyi (dakika) al
    toplam_yedi_gun_sure_dakika = CalismaOturumu.objects.filter(
        plan__kullanici=request.user,
        plan__tarih__gte=yedi_gun_oncesi,
        plan__tarih__lt=bugun
    ).aggregate(Sum('sure'))['sure__sum'] or 0

    # Ders bazlı istatistikleri hazırla (saat ve yüzde olarak)
    en_cok_calisilan_dersler_data = []
    for item in en_cok_calisilan_dersler_raw:
        ders_saat = item['total_sure'] / 60
        yuzde = (item['total_sure'] / toplam_yedi_gun_sure_dakika) * 100 if toplam_yedi_gun_sure_dakika > 0 else 0
        en_cok_calisilan_dersler_data.append({
            'ders__ad': item['ders__ad'],
            'toplam_sure': ders_saat,
            'yuzde': yuzde
        })

    context = {
        'bugun': bugun,
        'bugunun_plani': bugunun_plani,
        'bugunun_plani_toplam_saat': bugunun_plani_toplam_saat, # Context'e ekle
        'son_planlar': son_planlar,
        'gelecek_planlar': gelecek_planlar,
        'son_yedi_gun_toplam_saat': son_yedi_gun_toplam_saat, # Context'e ekle
        'en_cok_calisilan_dersler': en_cok_calisilan_dersler_data, # Context'e ekle
    }
    
    return render(request, 'yks/calisma_plani/calisma_plani_listesi.html', context)

@login_required
def calisma_plani_detay(request, plan_id):
    """Çalışma planı detaylarını gösterir"""
    plan = get_object_or_404(CalismaPlanı, id=plan_id, kullanici=request.user)
    oturumlar = CalismaOturumu.objects.filter(plan=plan).order_by('baslangic_saati')
    
    # Tamamlanan oturum sayısını hesapla
    tamamlanan_count = oturumlar.filter(tamamlandi=True).count()
    oturumlar.tamamlanan_count = tamamlanan_count
    
    # Planın tarihi bugünden önceyse geçmiş plan olarak işaretle
    gecmis_plan = plan.tarih < timezone.localdate()
    # Plan gelecek tarihli mi kontrol et
    gelecek_plan = plan.tarih > timezone.localdate()
    # Bugünün tarihini geç
    today = timezone.localdate()
    
    # Yeni oturum ekleme (sadece geçmiş plan değilse)
    if request.method == 'POST' and not gecmis_plan:
        form = CalismaOturumuForm(request.POST)
        if form.is_valid():
            oturum = form.save(commit=False)
            oturum.plan = plan
            
            # Form'un clean() metodunda hesaplanan sure değerini kullan
            oturum.sure = form.cleaned_data['sure']
            
            # Çakışan saatlere oturum eklemesini engelle
            baslangic_saati = form.cleaned_data['baslangic_saati']
            bitis_saati = form.cleaned_data['bitis_saati']
            
            # Aynı plan içinde çakışan saatlere oturumları kontrol et
            cakisan_oturumlar = CalismaOturumu.objects.filter(
                plan=plan
            ).filter(
                # Başlangıç saati mevcut oturumların arasında
                (Q(baslangic_saati__lt=bitis_saati) & Q(bitis_saati__gt=baslangic_saati))
            )
            
            if cakisan_oturumlar.exists():
                messages.error(request, 'Seçtiğiniz saat aralığı mevcut bir oturum ile çakışıyor!')
                context = {
                    'plan': plan,
                    'oturumlar': oturumlar,
                    'form': form,
                    'gecmis_plan': gecmis_plan,
                    'gelecek_plan': gelecek_plan,
                    'today': today,
                }
                return render(request, 'yks/calisma_plani/calisma_plani_detay.html', context)
            
            oturum.save()
            
            # Toplam çalışma süresini güncelle
            plan.toplam_calisma_suresi = CalismaOturumu.objects.filter(
                plan=plan
            ).aggregate(Sum('sure'))['sure__sum'] or 0
            plan.save()
            
            messages.success(request, 'Çalışma oturumu başarıyla eklendi.')
            return redirect('yks:calisma_plani_detay', plan_id=plan.id)
    else:
        form = CalismaOturumuForm()
    
    context = {
        'plan': plan,
        'oturumlar': oturumlar,
        'form': form,
        'gecmis_plan': gecmis_plan,  # Geçmiş plan mı bilgisini templatelere gönder
        'gelecek_plan': gelecek_plan,  # Gelecek plan mı bilgisini templatelere gönder
        'today': today,  # Bugünün tarihini templatelere gönder
    }
    
    return render(request, 'yks/calisma_plani/calisma_plani_detay.html', context)

@login_required
def calisma_plani_ekle(request):
    """Yeni çalışma planı ekleme görünümü"""

    # Bugün için zaten plan var mı kontrol et
    # bugun = timezone.localdate()
    # mevcut_plan = CalismaPlanı.objects.filter(
    #     kullanici=request.user,
    #     tarih=bugun
    # ).first()

    # if mevcut_plan:
    #     messages.info(request, f"Bugün için zaten bir çalışma planınız var. <a href='{mevcut_plan.get_absolute_url()}'>Görüntüle</a>")
    #     return redirect('yks:calisma_plani_listesi')

    if request.method == 'POST':
        form = CalismaPlanForm(data=request.POST, user=request.user)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.kullanici = request.user
            plan.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Çalışma planı başarıyla oluşturuldu.'})
            else:
                messages.success(request, 'Çalışma planı başarıyla oluşturuldu.')
                return redirect('yks:calisma_plani_detay', plan_id=plan.id)
    else:
        form = CalismaPlanForm(user=request.user)
    
    context = {
        'form': form,
    }

    # Eğer POST isteği geldiyse ve form geçerli değilse de aynı template'i render et
    if request.method == 'POST' and not form.is_valid():
        return render(request, 'yks/calisma_plani/calisma_plani_ekle.html', context)

    return render(request, 'yks/calisma_plani/calisma_plani_ekle.html', context)

@login_required
def oturum_sil(request, oturum_id):
    """Çalışma oturumu silme"""
    oturum = get_object_or_404(CalismaOturumu, id=oturum_id, plan__kullanici=request.user)
    plan_id = oturum.plan.id
    
    # Planın tarihi bugünden önceyse işlem yapma
    if oturum.plan.tarih < timezone.localdate():
        messages.error(request, 'Geçmiş tarihli planlardaki oturumlar silinemez.')
        return redirect('yks:calisma_plani_detay', plan_id=plan_id)
    
    if request.method == 'POST':
        oturum.delete()
        
        # Planın toplam süresini güncelle
        plan = oturum.plan
        plan.toplam_calisma_suresi = CalismaOturumu.objects.filter(
            plan=plan
        ).aggregate(Sum('sure'))['sure__sum'] or 0
        plan.save()
        
        messages.success(request, 'Çalışma oturumu başarıyla silindi.')
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True, 'message': 'Oturum başarıyla silindi.'})
        else:
            return redirect('yks:calisma_plani_detay', plan_id=plan_id)
    
    context = {
        'oturum': oturum,
    }
    
    return render(request, 'yks/calisma_plani/oturum_sil.html', context)

@login_required
@csrf_exempt
def oturum_tamamlandi_yap(request, oturum_id):
    """Çalışma oturumunu tamamlandı olarak işaretler (AJAX) """
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            oturum = get_object_or_404(CalismaOturumu, id=oturum_id, plan__kullanici=request.user)
            
            # Planın tarihi bugünden önceyse işlem yapma
            if oturum.plan.tarih < timezone.localdate():
                return JsonResponse({'success': False, 'message': 'Geçmiş tarihli planlardaki oturumlar güncellenemez.'}, status=403)
            
            # Planın tarihi gelecekteyse oturumları tamamlandı olarak işaretlemeye izin verme
            if oturum.plan.tarih > timezone.localdate():
                return JsonResponse({'success': False, 'message': 'Gelecek tarihli planlardaki oturumlar tamamlanamaz.'}, status=403)
                
            oturum.tamamlandi = True
            oturum.save()

            # Planın toplam süresini güncelle
            plan = oturum.plan
            plan.toplam_calisma_suresi = CalismaOturumu.objects.filter(
                plan=plan
            ).aggregate(Sum('sure'))['sure__sum'] or 0
            plan.save()
            
            # Güncel tamamlanan ve toplam oturum sayılarını al
            tamamlanan_oturum_sayisi = CalismaOturumu.objects.filter(
                plan=plan,
                tamamlandi=True
            ).count()
            toplam_oturum_sayisi = CalismaOturumu.objects.filter(plan=plan).count()

            return JsonResponse({
                'success': True,
                'message': 'Oturum tamamlandı olarak işaretlendi.',
                'tamamlanan_oturum_sayisi': tamamlanan_oturum_sayisi,
                'toplam_oturum_sayisi': toplam_oturum_sayisi,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'}, status=400)

@login_required
def dersler_json(request):
    """AJAX için dersleri JSON formatında döndürür"""
    dersler = Ders.objects.filter(aktif=True).order_by('alt_tur', 'ad')
    
    data = [
        {
            'id': ders.id,
            'ad': ders.ad,
            'kod': ders.kod,
            'alt_tur': ders.alt_tur.ad if ders.alt_tur else None
        }
        for ders in dersler
    ]
    
    return JsonResponse(data, safe=False)

@login_required
def konular_json(request, ders_id):
    """AJAX için belirli bir derse ait konuları JSON formatında döndürür"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders).order_by('sira_no')
    
    data = []
    
    for unite in uniteler:
        konular = Konu.objects.filter(unite=unite).order_by('sira_no')
        
        for konu in konular:
            data.append({
                'id': konu.id,
                'ad': konu.ad,
                'unite': unite.ad
            })
    
    return JsonResponse(data, safe=False)

# Hatırlatıcı Görünümleri
@login_required
def hatirlatici_listesi(request):
    """Kullanıcının hatırlatıcılarını listeler"""
    
    # Şu anki zaman (yerel saat dilimine göre)
    now = timezone.localtime()
    
    # Bugünün tarihi (saat bilgisini içermeden karşılaştırma yapmak için date() kullanıyoruz)
    bugun_date = now.date()
    
    # Bugünkü tüm hatırlatıcılar (şu andan öncekiler de dahil)
    bugunun_hatirlaticilari = Hatirlatici.objects.filter(
        kullanici=request.user,
        hatirlatma_tarihi__date=bugun_date
    ).order_by('hatirlatma_tarihi')
    
    # Geçmiş hatırlatıcılar (bugün ama şu andan önceki saatler + önceki günler)
    gecmis_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user,
        hatirlatma_tarihi__lt=now
    ).order_by('-hatirlatma_tarihi')
    
    # Yaklaşan hatırlatıcılar (şu andan sonrakiler)
    yaklasan_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user,
        hatirlatma_tarihi__gt=now
    ).order_by('hatirlatma_tarihi')
    
    # Bugün kategorisinde sadece şu andan sonraki hatırlatıcıları göster
    bugunun_hatirlaticilari_filtrelenmis = bugunun_hatirlaticilari.filter(
        hatirlatma_tarihi__gt=now
    )
    
    # Kullanıcının e-posta doğrulama durumunu al
    email_verified = request.user.userprofile.email_verified if hasattr(request.user, 'userprofile') else False

    context = {
        # İstatistik kartları için
        'toplam_hatirlatici_sayisi': Hatirlatici.objects.filter(kullanici=request.user).count(),
        'bugunku_hatirlatici_sayisi': bugunun_hatirlaticilari.count(),
        'yaklasan_hatirlatici_sayisi': yaklasan_hatirlaticilar.count(),
        
        # Tab içerikleri için
        'bugunun_hatirlaticilari': bugunun_hatirlaticilari_filtrelenmis,
        'yaklasan_hatirlaticilar_tab': yaklasan_hatirlaticilar,
        'gecmis_hatirlaticilar_tab': gecmis_hatirlaticilar,
        
        'email_verified': email_verified,
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_listesi.html', context)

@login_required
def hatirlatici_ekle(request):
    """Yeni hatırlatıcı ekle"""
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST)
        if form.is_valid():
            hatirlatici = form.save(commit=False)
            hatirlatici.kullanici = request.user
            
            # Tarihin timezone bilgisini kontrol et ve gerekirse düzelt
            from django.utils.timezone import is_aware, make_aware
            import pytz
            
            turkey_timezone = pytz.timezone('Europe/Istanbul')
            if not is_aware(hatirlatici.hatirlatma_tarihi):
                hatirlatici.hatirlatma_tarihi = make_aware(hatirlatici.hatirlatma_tarihi, turkey_timezone)
            
            # Debug bilgileri
            print(f"Kaydedilen tarih: {hatirlatici.hatirlatma_tarihi}")
            
            hatirlatici.save()
            
            # Celery görevi zamanla
            try:
                from .tasks import send_reminder_email
                send_reminder_email.apply_async(
                    args=[hatirlatici.id],
                    eta=hatirlatici.hatirlatma_tarihi
                )
                
                # Kullanıcıya bilgilendirici mesaj göster
                from django.utils.timezone import localtime
                yerel_tarih = localtime(hatirlatici.hatirlatma_tarihi)
                hatirlama_zamani = yerel_tarih.strftime("%d.%m.%Y %H:%M")
                messages.success(
                    request, 
                    f'Hatırlatıcı başarıyla eklendi. "{hatirlatici.baslik}" başlıklı hatırlatıcı için {hatirlama_zamani} tarihinde e-posta gönderilecek.'
                )
            except Exception as e:
                # Celery görevini zamanlarken bir hata oluşursa hata mesajı göster
                messages.warning(
                    request,
                    f'Hatırlatıcı eklendi, ancak otomatik e-posta gönderimi şu anda ayarlanamadı: {str(e)}'
                )
            
            return redirect('yks:hatirlatici_listesi')
    else:
        form = HatirlaticiForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_ekle.html', context)

@login_required
def hatirlatici_duzenle(request, hatirlatici_id):
    """Hatırlatıcı düzenle"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)
    eski_tarih = hatirlatici.hatirlatma_tarihi
    eski_aktif = hatirlatici.aktif
    
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST, instance=hatirlatici)
        if form.is_valid():
            # Hatırlatıcının önceki durumlarını kaydet
            hatirlatici = form.save(commit=False)
            
            # Tarihin timezone bilgisini kontrol et ve gerekirse düzelt
            from django.utils.timezone import is_aware, make_aware
            import pytz
            
            turkey_timezone = pytz.timezone('Europe/Istanbul')
            if not is_aware(hatirlatici.hatirlatma_tarihi):
                hatirlatici.hatirlatma_tarihi = make_aware(hatirlatici.hatirlatma_tarihi, turkey_timezone)
            
            # Debug bilgileri
            print(f"Düzenlenen tarih: {hatirlatici.hatirlatma_tarihi}")
            
            hatirlatici.save()
            
            # Eğer tarih veya aktiflik değiştiyse Celery görevini güncelle
            if eski_tarih != hatirlatici.hatirlatma_tarihi or eski_aktif != hatirlatici.aktif:
                try:
                    # Yeni görevi zamanla (eski görev zaten devre dışı kalacak)
                    from .tasks import send_reminder_email
                    
                    # Eğer hatırlatıcı hala aktifse ve gönderilmediyse
                    if hatirlatici.aktif and not hatirlatici.sent:
                        # Zamanı geçmediyse yeni görev planla
                        if hatirlatici.hatirlatma_tarihi > timezone.now():
                            send_reminder_email.apply_async(
                                args=[hatirlatici.id],
                                eta=hatirlatici.hatirlatma_tarihi
                            )
                            from django.utils.timezone import localtime
                            yerel_tarih = localtime(hatirlatici.hatirlatma_tarihi)
                            hatirlama_zamani = yerel_tarih.strftime("%d.%m.%Y %H:%M")
                            messages.success(
                                request, 
                                f'Hatırlatıcı güncellendi. "{hatirlatici.baslik}" başlıklı hatırlatıcı için {hatirlama_zamani} tarihinde e-posta gönderilecek.'
                            )
                        else:
                            messages.warning(
                                request,
                                f'Hatırlatıcı güncellendi, ancak belirlediğiniz zaman geçmiş olduğu için e-posta gönderilmeyecek.'
                            )
                    else:
                        if not hatirlatici.aktif:
                            messages.info(request, 'Hatırlatıcı pasif durumda olduğu için e-posta gönderilmeyecek.')
                        elif hatirlatici.sent:
                            messages.info(request, 'Bu hatırlatıcı için zaten e-posta gönderilmiş.')
                except Exception as e:
                    messages.warning(
                        request,
                        f'Hatırlatıcı güncellendi, ancak otomatik e-posta gönderimi şu anda ayarlanamadı: {str(e)}'
                    )
            else:
                messages.success(request, 'Hatırlatıcı başarıyla güncellendi.')
            
            return redirect('yks:hatirlatici_listesi')
    else:
        form = HatirlaticiForm(instance=hatirlatici)
    
    context = {
        'form': form,
        'hatirlatici': hatirlatici,
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_duzenle.html', context)

@login_required
def hatirlatici_sil(request, hatirlatici_id):
    """AJAX ile hatırlatıcı silme"""
    # Kullanıcının sadece kendi hatırlatıcılarını silebildiğinden emin ol
    try:
        hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)
    except Http404:
        # Eğer hatırlatıcı bulunamazsa veya kullanıcıya ait değilse 404 döndür
        return JsonResponse({'success': False, 'message': 'Hatırlatıcı bulunamadı veya silme yetkiniz yok.'}, status=404)


    if request.method == 'POST':
        try:
            hatirlatici.delete()
            # messages.success(request, 'Hatırlatıcı başarıyla silindi.') # Kaldırıldı
            # return redirect('yks:hatirlatici_listesi') # Kaldırıldı
            return JsonResponse({'success': True, 'message': 'Hatırlatıcı başarıyla silindi.'})
        except Exception as e:
            # Silme sırasında bir hata oluşursa hata yanıtı döndür
            return JsonResponse({'success': False, 'message': f'Hatırlatıcı silinirken bir hata oluştu: {str(e)}'}, status=500)

    # Eğer istek POST değilse hata döndür
    return JsonResponse({'success': False, 'message': 'Geçersiz istek metodu.'}, status=405)

@login_required
def hatirlatici_durum_guncelle(request, hatirlatici_id):
    """Hatırlatıcı durumunu güncelleme (AJAX POST) """

    # Sadece AJAX POST isteklerini kabul et. Başka bir istek gelirse hata döndür.
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'
    if not (request.method == 'POST' and is_ajax):
        return JsonResponse({
            'success': False,
            'message': 'Bu işlem sadece AJAX POST istekleri ile desteklenmektedir.'
        }, status=405) # Method Not Allowed

    # Eğer buraya ulaştıysak, bu geçerli bir AJAX POST isteğidir.
    import json
    try:
        # Kullanıcının sadece kendi hatırlatıcılarını güncelleyebildiğinden emin ol
        hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)

        # JSON verisini oku
        data = json.loads(request.body)
        aktif = data.get('aktif') # JSON'dan aktif değerini al

        # 'aktif' değeri None değilse ve boolean ise devam et
        if aktif is not None and isinstance(aktif, bool):
            hatirlatici.aktif = aktif
            hatirlatici.save()

            # Başarılı JSON yanıtı döndür
            return JsonResponse({
                'success': True,
                'message': 'Hatırlatıcı durumu başarıyla güncellendi.'
            })
        else:
             # Geçersiz veya eksik veri durumunda hata yanıtı
             return JsonResponse({'success': False, 'message': 'Geçersiz veya eksik veri sağlandı.'}, status=400) # Bad Request

    except Http404:
         # Hatırlatıcı bulunamazsa veya kullanıcıya ait değilse 404 yanıtı
         return JsonResponse({'success': False, 'message': 'Hatırlatıcı bulunamadı veya güncelleme yetkiniz yok.'}, status=404)
    except json.JSONDecodeError:
         # Geçersiz JSON formatı durumunda hata yanıtı
         return JsonResponse({'success': False, 'message': 'Geçersiz JSON formatı.'}, status=400)
    except Exception as e:
         # Diğer tüm hatalar için genel hata yanıtı
         # Loglama yapılmalı: logger.error(f"Hatırlatıcı durum güncelleme hatası: {e}", exc_info=True)
         return JsonResponse({'success': False, 'message': f'Beklenmedik bir hata oluştu: {str(e)}'}, status=500) # Internal Server Error

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

@login_required
def hedef_turu_sec(request):
    return render(request, 'yks/hedef_belirleme/hedef_turu_sec.html')

@login_required
def soru_cozum_hedef_ekle(request):
    """Soru çözümü hedefi ekleme görünümü"""
    if request.method == 'POST':
        try:
            # Hedef Durumlarını kontrol et/oluştur
            aktif_durum, _ = HedefDurum.objects.get_or_create(ad='Aktif')
            tamamlandi_durum, _ = HedefDurum.objects.get_or_create(ad='Tamamlandı')
            tamamlanmadi_durum, _ = HedefDurum.objects.get_or_create(ad='Tamamlanmadı')

            ders_id = request.POST.get('ders')
            toplam_soru = request.POST.get('toplam_soru')
            baslangic_tarihi = request.POST.get('baslangic_tarihi')
            bitis_tarihi = request.POST.get('bitis_tarihi')
            aciklama = request.POST.get('aciklama')
            hedef_turu_ad = request.POST.get('hedef_turu')
            ders = get_object_or_404(Ders, id=ders_id)
            hedef_turu = HedefTuru.objects.get(ad=hedef_turu_ad)
            hedef = Hedef.objects.create(
                kullanici=request.user,
                baslik=f"{ders.ad} Soru Çözümü Hedefi",
                aciklama=aciklama,
                tur=hedef_turu,
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi,
                ders=ders,
                hedef_durum=aktif_durum # Yeni hedefin durumu varsayılan olarak Aktif
            )
            SoruCozumHedefi.objects.create(
                hedef=hedef,
                toplam_soru=toplam_soru,
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Soru çözümü hedefi başarıyla oluşturuldu.'})
            else:
                messages.success(request, 'Soru çözümü hedefi başarıyla oluşturuldu.')
                return redirect('yks:hedef_listesi')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            else:
                messages.error(request, f'Hedef oluşturulurken bir hata oluştu: {str(e)}')
    dersler = Ders.objects.filter(aktif=True).order_by('ad')
    context = {
        'dersler': dersler,
    }
    return render(request, 'yks/hedef_belirleme/soru_cozum_hedef_ekle.html', context)

@login_required
def konu_takip_hedef_ekle(request):
    """Konu takibi hedefi ekleme görünümü"""
    if request.method == 'POST':
        try:
            # Hedef Durumlarını kontrol et/oluştur
            aktif_durum, _ = HedefDurum.objects.get_or_create(ad='Aktif')
            tamamlandi_durum, _ = HedefDurum.objects.get_or_create(ad='Tamamlandı')
            tamamlanmadi_durum, _ = HedefDurum.objects.get_or_create(ad='Tamamlanmadı')
            
            ders_id = request.POST.get('ders')
            konular = request.POST.getlist('konular')
            baslangic_tarihi = request.POST.get('baslangic_tarihi')
            bitis_tarihi = request.POST.get('bitis_tarihi')
            aciklama = request.POST.get('aciklama')
            hedef_turu_ad = request.POST.get('hedef_turu')
            ders = get_object_or_404(Ders, id=ders_id)
            print('Formdan gelen:', hedef_turu_ad)
            print('DB:', list(HedefTuru.objects.values_list('ad', flat=True)))
            hedef_turu = HedefTuru.objects.get(ad=hedef_turu_ad)
            hedef = Hedef.objects.create(
                kullanici=request.user,
                baslik=f"{ders.ad} Konu Takibi Hedefi",
                aciklama=aciklama,
                tur=hedef_turu,
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi,
                ders=ders,
                hedef_durum=aktif_durum # Yeni hedefin durumu varsayılan olarak Aktif
            )
            konu_takip_hedefi = KonuTakipHedefi.objects.create(
                hedef=hedef,
                ders=ders,
                baslangic_tarihi=baslangic_tarihi,
                bitis_tarihi=bitis_tarihi
            )
            for konu_id in konular:
                konu = get_object_or_404(Konu, id=konu_id)
                KonuTakipHedefKonu.objects.create(
                    konu_takip_hedefi=konu_takip_hedefi,
                    konu=konu
                )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Konu takibi hedefi başarıyla oluşturuldu.'})
            else:
                messages.success(request, 'Konu takibi hedefi başarıyla oluşturuldu.')
                return redirect('yks:hedef_listesi')
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': str(e)}, status=400)
            else:
                messages.error(request, f'Hedef oluşturulurken bir hata oluştu: {str(e)}')
    dersler = Ders.objects.filter(aktif=True).order_by('ad')
    context = {
        'dersler': dersler,
    }
    return render(request, 'yks/hedef_belirleme/konu_takip_hedef_ekle.html', context)

@login_required
def hedef_ilerleme_kaydet(request, hedef_id):
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
    # Soru çözüm hedefi mi?
    if hasattr(hedef, 'soru_cozum_detay'):
        return redirect('yks:soru_cozum_ilerleme', hedef_id=hedef.id)
    # Konu takip hedefi mi?
    elif hasattr(hedef, 'konu_takip_detay'):
        return redirect('yks:konu_takip_ilerleme', hedef_id=hedef.id)
    # Diğer türler için hedef düzenleye yönlendir
    return redirect('yks:hedef_duzenle', hedef_id=hedef.id)

@login_required
def soru_cozum_ilerleme(request, hedef_id):
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
    try:
        detay = hedef.soru_cozum_detay
    except Exception:
        messages.error(request, 'Bu hedef bir soru çözüm hedefi değildir.')
        return redirect('yks:hedef_listesi')
    if request.method == 'POST':
        try:
            cozulmus_soru = int(request.POST.get('cozulmus_soru', 0))
            detay.cozulmus_soru = max(0, min(cozulmus_soru, detay.toplam_soru))
            detay.save()
            messages.success(request, 'Çözülen soru sayısı güncellendi.')
            return redirect('yks:hedef_listesi')
        except Exception as e:
            messages.error(request, f'Güncelleme sırasında hata: {str(e)}')
    ilerleme = detay.ilerleme_orani()
    context = {
        'hedef': hedef,
        'detay': detay,
        'ilerleme': ilerleme,
    }
    return render(request, 'yks/hedef_belirleme/soru_cozum_ilerleme.html', context)

@login_required
def konu_takip_ilerleme(request, hedef_id):
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
    try:
        detay = hedef.konu_takip_detay
    except Exception:
        messages.error(request, 'Bu hedef bir konu takip hedefi değildir.')
        return redirect('yks:hedef_listesi')
    konular = detay.konular.all().select_related('konu')
    if request.method == 'POST':
        tamamlanan_konular = request.POST.getlist('tamamlanan_konular')
        detay.konular.all().update(tamamlandi=False)
        if tamamlanan_konular:
            detay.konular.filter(konu_id__in=tamamlanan_konular).update(tamamlandi=True)
        messages.success(request, 'Konu ilerlemesi güncellendi.')
        return redirect('yks:hedef_listesi')
    toplam = konular.count()
    tamamlanan = konular.filter(tamamlandi=True).count()
    ilerleme = int((tamamlanan / toplam) * 100) if toplam > 0 else 0
    context = {
        'hedef': hedef,
        'detay': detay,
        'konular': konular,
        'ilerleme': ilerleme,
    }
    return render(request, 'yks/hedef_belirleme/konu_takip_ilerleme.html', context)

@login_required
@csrf_exempt
def calisma_oturum_geri_al(request, oturum_id):
    """Tamamlanmış çalışma oturumunu geri al (AJAX)"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        try:
            oturum = get_object_or_404(CalismaOturumu, id=oturum_id, plan__kullanici=request.user)
            
            # Planın tarihi bugünden önceyse işlem yapma
            if oturum.plan.tarih < timezone.localdate():
                return JsonResponse({'success': False, 'message': 'Geçmiş tarihli planlardaki oturumlar güncellenemez.'}, status=403)
            
            # Planın tarihi gelecekteyse oturumlar zaten tamamlanmış olamaz, durumu değiştirmeye izin verme
            if oturum.plan.tarih > timezone.localdate():
                return JsonResponse({'success': False, 'message': 'Gelecek tarihli planlardaki oturumlar güncellenemez.'}, status=403)
            
            oturum.tamamlandi = False
            oturum.save()
            
            # Plan toplam süresini güncelle
            plan = oturum.plan
            plan.toplam_calisma_suresi = CalismaOturumu.objects.filter(
                plan=plan
            ).aggregate(Sum('sure'))['sure__sum'] or 0
            plan.save()
            
            # Güncel tamamlanan ve toplam oturum sayılarını al
            tamamlanan_oturum_sayisi = CalismaOturumu.objects.filter(
                plan=plan,
                tamamlandi=True
            ).count()
            toplam_oturum_sayisi = CalismaOturumu.objects.filter(plan=plan).count()

            return JsonResponse({
                'success': True,
                'message': 'Oturum durumu geri alındı.',
                'tamamlanan_oturum_sayisi': tamamlanan_oturum_sayisi,
                'toplam_oturum_sayisi': toplam_oturum_sayisi,
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek.'}, status=400)

@login_required
def profil(request):
    """Kullanıcı profil sayfası"""
    # Kullanıcının profilini al veya oluştur
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
            return redirect('yks:profil')
    else:
        form = UserProfileForm(instance=profile)
    
    context = {
        'form': form,
        'profile': profile
    }
    
    return render(request, 'yks/profil.html', context)

# Deneme Sınavı URL'leri
@login_required
def deneme_sinav_listesi(request):
    """Kullanıcının kaydettiği deneme sınavı sonuçlarını listeler."""
    deneme_sonuclari = DenemeSinavSonucu.objects.filter(kullanici=request.user).order_by('-sinav_tarihi', '-olusturma_tarihi')
    
    context = {
        'deneme_sonuclari': deneme_sonuclari,
    }
    
    return render(request, 'yks/deneme_sinav_listesi.html', context)

@login_required
def deneme_sinav_ekle_sinav_secim(request):
    """Yeni deneme sınavı sonucu eklemek için sınav türü (TYT, AYT, YDT) seçim sayfasını gösterir."""
    # sinav_turu_id'si 1 olan SinavAltTur verilerini çek (TYT, AYT, YDT)
    sinav_alt_turleri = SinavAltTur.objects.filter(sinav_turu_id=1).order_by('ad')
    
    context = {
        'sinav_alt_turleri': sinav_alt_turleri,
    }
    
    return render(request, 'yks/deneme_sinav_ekle_sinav_secim.html', context)

@login_required
def deneme_sinav_ekle_ders_sonuclari(request, sinav_kodu):
    try:
        sinav_alt_tur = get_object_or_404(SinavAltTur, kod=sinav_kodu)
        dersler = Ders.objects.filter(alt_tur=sinav_alt_tur).order_by('ad')
    except:
        return redirect('yks:deneme_sinav_ekle_sinav_secim')

    fazla_girilen_dersler = []
    hata_mesaji = None
    if request.method == 'POST':
        validation_successful = True
        for ders in dersler:
            dogru_key = f'dogru_{ders.id}'
            yanlis_key = f'yanlis_{ders.id}'
            bos_key = f'bos_{ders.id}'
            try:
                dogru = int(request.POST.get(dogru_key, 0))
            except ValueError:
                dogru = 0
            try:
                yanlis = int(request.POST.get(yanlis_key, 0))
            except ValueError:
                yanlis = 0
            try:
                bos = int(request.POST.get(bos_key, 0))
            except ValueError:
                bos = 0
            girilen_toplam = dogru + yanlis + bos
            toplam_soru_sayisi = ders.soru_sayisi
            if girilen_toplam > toplam_soru_sayisi:
                fazla_girilen_dersler.append({'id': ders.id, 'ad': ders.ad, 'max': toplam_soru_sayisi})
                validation_successful = False
        if validation_successful:
            deneme_sonucu = DenemeSinavSonucu.objects.create(
                kullanici=request.user,
                sinav_alt_tur=sinav_alt_tur,
                sinav_tarihi=timezone.now().date()
            )
            for ders in dersler:
                try:
                    dogru = int(request.POST.get(f'dogru_{ders.id}', 0))
                except ValueError:
                    dogru = 0
                try:
                    yanlis = int(request.POST.get(f'yanlis_{ders.id}', 0))
                except ValueError:
                    yanlis = 0
                try:
                    bos = int(request.POST.get(f'bos_{ders.id}', 0))
                except ValueError:
                    bos = 0
                toplam_soru_sayisi = ders.soru_sayisi
                if dogru + yanlis + bos == 0:
                    bos = toplam_soru_sayisi
                    dogru = 0
                    yanlis = 0
                elif dogru + yanlis + bos < toplam_soru_sayisi:
                    bos = toplam_soru_sayisi - (dogru + yanlis)
                if dogru + yanlis + bos > toplam_soru_sayisi:
                    continue
                DenemeSinavDersSonucu.objects.create(
                    deneme_sinav_sonucu=deneme_sonucu,
                    ders=ders,
                    dogru=dogru,
                    yanlis=yanlis,
                    bos=bos
                )
            return redirect('yks:deneme_sinav_listesi')
        else:
            hata_mesaji = 'Bazı derslerde toplam giriş, dersin soru sayısından fazla!'
    context = {
        'sinav_alt_tur': sinav_alt_tur,
        'dersler': dersler,
        'submitted_data': request.POST if request.method == 'POST' else None,
        'fazla_girilen_dersler': fazla_girilen_dersler,
        'hata_mesaji': hata_mesaji,
    }
    return render(request, 'yks/deneme_sinav_ekle_ders_sonuclari.html', context)

@login_required
def deneme_sinav_detay(request, sonuc_id):
    """Belirli bir deneme sınavı sonucunun detaylarını gösterir."""
    # Deneme sınavı sonucunu kullanıcıya ait olup olmadığını kontrol ederek getir
    deneme_sonucu = get_object_or_404(DenemeSinavSonucu, id=sonuc_id, kullanici=request.user)

    # Bu deneme sınavına ait ders sonuçlarını getir
    ders_sonuclari = DenemeSinavDersSonucu.objects.filter(deneme_sinav_sonucu=deneme_sonucu).order_by('ders__ad')

    context = {
        'deneme_sonucu': deneme_sonucu,
        'ders_sonuclari': ders_sonuclari,
    }

    return render(request, 'yks/deneme_sinav_detay.html', context)

@login_required
def sinav_analizleri(request):
    """Sınav Analizleri sayfası görünümü"""
    context = {}
    return render(request, 'yks/sinav_analizleri/index.html', context)

@login_required
def pomodoro_timer(request):
    """Pomodoro Çalışma Tekniği sayfası görünümü"""
    context = {}
    return render(request, 'yks/pomodoro/index.html', context)

@login_required
def motivasyon_sistemi(request):
    """Motivasyon Sistemi sayfası görünümü"""
    context = {}
    return render(request, 'yks/motivasyon/index.html', context)