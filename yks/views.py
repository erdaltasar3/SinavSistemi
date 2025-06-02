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
from .models import (
    YKSOturum, 
    KonuTakip, 
    Hedef, 
    HedefTuru, 
    CalismaPlanı, 
    CalismaOturumu, 
    Gorev, 
    Hatirlatici,
    SoruCozumHedefi,
    KonuTakipHedefi,
    KonuTakipHedefKonu
)
from .forms import (
    HedefForm,
    HedefDuzenleForm,
    CalismaPlanForm,
    CalismaOturumuForm,
    GorevForm,
    GorevDuzenleForm,
    HatirlaticiForm
)
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

# Hedef Belirleme ve Takip Görünümleri
@login_required
def hedef_listesi(request):
    """
    Kullanıcının hedeflerini sekme (aktif, tamamlanan, tamamlanmayan) ve tür (Günlük, Haftalık, Özel) filtrelerine göre listeler
    """
    # Parametreleri al
    sekme = request.GET.get('sekme', 'aktif')
    tur = request.GET.get('tur', 'Günlük')

    # Temel queryset
    hedefler = Hedef.objects.filter(kullanici=request.user)

    # Sekmeye göre filtrele
    if sekme == 'aktif':
        hedefler = hedefler.filter(durum=Hedef.DURUM_AKTIF)
    elif sekme == 'tamamlanan':
        hedefler = hedefler.filter(durum=Hedef.DURUM_TAMAMLANDI)
    elif sekme == 'tamamlanmayan':
        hedefler = hedefler.exclude(durum=Hedef.DURUM_TAMAMLANDI)
    else:
        hedefler = hedefler.filter(durum=Hedef.DURUM_AKTIF)

    # Tür filtresi uygula
    hedefler = hedefler.filter(tur__ad=tur)

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
        
        # Soru çözümü hedefi mi kontrol et
        try:
            soru_cozum = hedef.soru_cozum_detay
            hedef_data['tip'] = 'soru_cozum'
            hedef_data['ilerleme'] = soru_cozum.ilerleme_orani()
            hedef_data['toplam_soru'] = soru_cozum.toplam_soru
            hedef_data['cozulmus_soru'] = soru_cozum.cozulmus_soru
        except:
            pass
        
        # Konu takibi hedefi mi kontrol et
        try:
            konu_takip = hedef.konu_takip_detay
            hedef_data['tip'] = 'konu_takip'
            hedef_data['ilerleme'] = konu_takip.ilerleme_orani()
            hedef_data['toplam_konu'] = konu_takip.konular.count()
            hedef_data['tamamlanan_konu'] = konu_takip.konular.filter(tamamlandi=True).count()
        except:
            pass
        
        hedef_listesi.append(hedef_data)

    # İstatistikler
    toplam_hedef = Hedef.objects.filter(kullanici=request.user).count()
    tamamlanan_sayisi = Hedef.objects.filter(
        kullanici=request.user, 
        durum=Hedef.DURUM_TAMAMLANDI
    ).count()
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
    """Hedef düzenleme görünümü"""
    hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
    
    if request.method == 'POST':
        try:
            if hasattr(hedef, 'sorucozumhedefi'):
                # Soru çözümü hedefi güncelleme
                cozulmus_soru = int(request.POST.get('cozulmus_soru', 0))
                hedef.sorucozumhedefi.cozulmus_soru = cozulmus_soru
                hedef.sorucozumhedefi.save()
                
                # Hedef durumunu güncelle
                if cozulmus_soru >= hedef.sorucozumhedefi.toplam_soru:
                    hedef.durum = 'Tamamlandı'
                hedef.save()
                
                messages.success(request, 'Soru çözümü ilerlemesi başarıyla güncellendi.')
            elif hasattr(hedef, 'konutakiphedefi'):
                # Konu takibi hedefi güncelleme
                tamamlanan_konular = request.POST.getlist('tamamlanan_konular')
                
                # Tüm konuları tamamlanmamış olarak işaretle
                hedef.konutakiphedefi.konutakiphedefkonu_set.all().update(tamamlandi=False)
                
                # Seçili konuları tamamlanmış olarak işaretle
                if tamamlanan_konular:
                    hedef.konutakiphedefi.konutakiphedefkonu_set.filter(konu_id__in=tamamlanan_konular).update(tamamlandi=True)
                
                # Hedef durumunu güncelle
                tamamlanan_sayisi = hedef.konutakiphedefi.konutakiphedefkonu_set.filter(tamamlandi=True).count()
                toplam_konu = hedef.konutakiphedefi.konutakiphedefkonu_set.count()
                
                if tamamlanan_sayisi == toplam_konu:
                    hedef.durum = 'Tamamlandı'
                hedef.save()
                
                messages.success(request, 'Konu takibi ilerlemesi başarıyla güncellendi.')
            
            return redirect('yks:hedef_listesi')
        except Exception as e:
            messages.error(request, f'İlerleme güncellenirken bir hata oluştu: {str(e)}')
    
    # Hedef tipini ve ilgili verileri belirle
    if hasattr(hedef, 'sorucozumhedefi'):
        hedef.tip = 'soru_cozum'
        hedef.ilerleme = hedef.sorucozumhedefi.ilerleme_orani()
        hedef.cozulmus_soru = hedef.sorucozumhedefi.cozulmus_soru
        hedef.toplam_soru = hedef.sorucozumhedefi.toplam_soru
    elif hasattr(hedef, 'konutakiphedefi'):
        hedef.tip = 'konu_takip'
        hedef.ilerleme = hedef.konutakiphedefi.ilerleme_orani()
        hedef.konular = hedef.konutakiphedefi.konutakiphedefkonu_set.all().select_related('konu')
    
    return render(request, 'yks/hedef_belirleme/hedef_duzenle.html', {
        'hedef': hedef
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
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        hedef = get_object_or_404(Hedef, id=hedef_id, kullanici=request.user)
        
        yeni_durum = request.POST.get('durum')
        yeni_oran = request.POST.get('tamamlanma_orani')
        
        if yeni_durum:
            hedef.durum = yeni_durum
        
        if yeni_oran:
            try:
                oran = int(yeni_oran)
                if 0 <= oran <= 100:
                    hedef.tamamlanma_orani = oran
                    
                    # Eğer oran 100 ise otomatik olarak tamamlandı olarak işaretle
                    if oran == 100:
                        hedef.durum = Hedef.DURUM_TAMAMLANDI
            except ValueError:
                pass
        
        hedef.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Hedef durumu güncellendi.'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    }, status=400)

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
    
    context = {
        'bugun': bugun,
        'bugunun_plani': bugunun_plani,
        'son_planlar': son_planlar,
        'gelecek_planlar': gelecek_planlar,
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
    
    # Yeni oturum ekleme
    if request.method == 'POST':
        form = CalismaOturumuForm(request.POST)
        if form.is_valid():
            oturum = form.save(commit=False)
            oturum.plan = plan
            
            # Form'un clean() metodunda hesaplanan sure değerini kullan
            oturum.sure = form.cleaned_data['sure']
            
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
    }
    
    return render(request, 'yks/calisma_plani/calisma_plani_detay.html', context)

@login_required
def calisma_plani_ekle(request):
    """Yeni çalışma planı ekleme görünümü"""
    
    # Bugün için zaten plan var mı kontrol et
    bugun = timezone.localdate()
    mevcut_plan = CalismaPlanı.objects.filter(
        kullanici=request.user,
        tarih=bugun
    ).first()
    
    if mevcut_plan:
        messages.info(request, f"Bugün için zaten bir çalışma planınız var. <a href='{mevcut_plan.get_absolute_url()}'>Görüntüle</a>")
        return redirect('yks:calisma_plani_listesi')
    
    if request.method == 'POST':
        form = CalismaPlanForm(request.POST)
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
        form = CalismaPlanForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'yks/calisma_plani/calisma_plani_ekle.html', context)

@login_required
def oturum_sil(request, oturum_id):
    """Çalışma oturumu silme"""
    oturum = get_object_or_404(CalismaOturumu, id=oturum_id, plan__kullanici=request.user)
    plan_id = oturum.plan.id
    
    if request.method == 'POST':
        oturum.delete()
        
        # Planın toplam süresini güncelle
        plan = oturum.plan
        plan.toplam_calisma_suresi = CalismaOturumu.objects.filter(
            plan=plan
        ).aggregate(Sum('sure'))['sure__sum'] or 0
        plan.save()
        
        messages.success(request, 'Çalışma oturumu başarıyla silindi.')
        return redirect('yks:calisma_plani_detay', plan_id=plan_id)
    
    context = {
        'oturum': oturum,
    }
    
    return render(request, 'yks/calisma_plani/oturum_sil.html', context)

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

# Görev (To-Do) Yönetimi Görünümleri
@login_required
def gorev_listesi(request):
    """Kullanıcının görevlerini listeler"""
    # Bekleyen görevler
    bekleyen_gorevler = Gorev.objects.filter(
        kullanici=request.user,
        durum=Gorev.DURUM_BEKLIYOR
    ).order_by('son_tarih', '-oncelik')
    
    # Tamamlanan görevler
    tamamlanan_gorevler = Gorev.objects.filter(
        kullanici=request.user,
        durum=Gorev.DURUM_TAMAMLANDI
    ).order_by('-guncelleme_tarihi')[:10]  # Son 10 tamamlanan görev
    
    # Ertelenen görevler
    ertelenen_gorevler = Gorev.objects.filter(
        kullanici=request.user,
        durum=Gorev.DURUM_ERTELENDI
    ).order_by('son_tarih')
    
    # İstatistikler
    toplam_gorev = Gorev.objects.filter(kullanici=request.user).count()
    tamamlanan_sayisi = Gorev.objects.filter(
        kullanici=request.user,
        durum=Gorev.DURUM_TAMAMLANDI
    ).count()
    
    tamamlanma_yuzdesi = 0
    if toplam_gorev > 0:
        tamamlanma_yuzdesi = (tamamlanan_sayisi / toplam_gorev) * 100
    
    context = {
        'bekleyen_gorevler': bekleyen_gorevler,
        'tamamlanan_gorevler': tamamlanan_gorevler,
        'ertelenen_gorevler': ertelenen_gorevler,
        'toplam_gorev': toplam_gorev,
        'tamamlanan_sayisi': tamamlanan_sayisi,
        'tamamlanma_yuzdesi': tamamlanma_yuzdesi,
    }
    
    return render(request, 'yks/gorevler/gorev_listesi.html', context)

@login_required
def gorev_ekle(request):
    """Yeni görev ekleme görünümü"""
    if request.method == 'POST':
        form = GorevForm(request.POST)
        if form.is_valid():
            gorev = form.save(commit=False)
            gorev.kullanici = request.user
            gorev.save()
            messages.success(request, 'Görev başarıyla eklendi.')
            return redirect('yks:gorev_listesi')
    else:
        form = GorevForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'yks/gorevler/gorev_ekle.html', context)

@login_required
def gorev_duzenle(request, gorev_id):
    """Görev düzenleme görünümü"""
    gorev = get_object_or_404(Gorev, id=gorev_id, kullanici=request.user)
    
    if request.method == 'POST':
        form = GorevDuzenleForm(request.POST, instance=gorev)
        if form.is_valid():
            form.save()
            messages.success(request, 'Görev başarıyla güncellendi.')
            return redirect('yks:gorev_listesi')
    else:
        form = GorevDuzenleForm(instance=gorev)
    
    context = {
        'form': form,
        'gorev': gorev,
    }
    
    return render(request, 'yks/gorevler/gorev_duzenle.html', context)

@login_required
def gorev_sil(request, gorev_id):
    """Görev silme görünümü"""
    gorev = get_object_or_404(Gorev, id=gorev_id, kullanici=request.user)
    
    if request.method == 'POST':
        gorev.delete()
        messages.success(request, 'Görev başarıyla silindi.')
        return redirect('yks:gorev_listesi')
    
    context = {
        'gorev': gorev,
    }
    
    return render(request, 'yks/gorevler/gorev_sil.html', context)

@login_required
def gorev_durum_guncelle(request, gorev_id):
    """AJAX ile görev durumunu güncelleme"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        gorev = get_object_or_404(Gorev, id=gorev_id, kullanici=request.user)
        
        yeni_durum = request.POST.get('durum')
        
        if yeni_durum:
            gorev.durum = yeni_durum
            gorev.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Görev durumu güncellendi.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    }, status=400)

# Hatırlatıcı Görünümleri
@login_required
def hatirlatici_listesi(request):
    """Kullanıcının hatırlatıcılarını listeler"""
    # Aktif hatırlatıcılar
    aktif_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user,
        aktif=True,
        hatirlatma_tarihi__gte=timezone.now()
    ).order_by('hatirlatma_tarihi')
    
    # Yaklaşan hatırlatıcılar (bugün ve yakın gelecek)
    bugun = timezone.now()
    yaklasan_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user,
        aktif=True,
        hatirlatma_tarihi__date=bugun.date()
    ).order_by('hatirlatma_tarihi')
    
    # Geçmiş hatırlatıcılar
    gecmis_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user,
        hatirlatma_tarihi__lt=bugun
    ).order_by('-hatirlatma_tarihi')[:10]  # Son 10 geçmiş hatırlatıcı
    
    context = {
        'aktif_hatirlaticilar': aktif_hatirlaticilar,
        'yaklasan_hatirlaticilar': yaklasan_hatirlaticilar,
        'gecmis_hatirlaticilar': gecmis_hatirlaticilar,
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_listesi.html', context)

@login_required
def hatirlatici_ekle(request):
    """Yeni hatırlatıcı ekleme görünümü"""
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST)
        if form.is_valid():
            hatirlatici = form.save(commit=False)
            hatirlatici.kullanici = request.user
            hatirlatici.save()
            messages.success(request, 'Hatırlatıcı başarıyla eklendi.')
            return redirect('yks:hatirlatici_listesi')
    else:
        form = HatirlaticiForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_ekle.html', context)

@login_required
def hatirlatici_duzenle(request, hatirlatici_id):
    """Hatırlatıcı düzenleme görünümü"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)
    
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST, instance=hatirlatici)
        if form.is_valid():
            form.save()
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
    """Hatırlatıcı silme görünümü"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)
    
    if request.method == 'POST':
        hatirlatici.delete()
        messages.success(request, 'Hatırlatıcı başarıyla silindi.')
        return redirect('yks:hatirlatici_listesi')
    
    context = {
        'hatirlatici': hatirlatici,
    }
    
    return render(request, 'yks/hatirlaticilar/hatirlatici_sil.html', context)

@login_required
def hatirlatici_durum_guncelle(request, hatirlatici_id):
    """Hatırlatıcı durumunu güncelleme (AJAX veya normal form)"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id, kullanici=request.user)
    
    if request.method == 'POST':
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        # İstek AJAX veya normal form olabilir
        if 'aktif' in request.POST:
            aktif_value = request.POST.get('aktif')
            # String 'true' veya 'false' değerini bool'a çevir
            aktif = aktif_value.lower() == 'true'
            hatirlatici.aktif = aktif
            hatirlatici.save()
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': 'Hatırlatıcı durumu güncellendi.'
                })
            else:
                status_text = "aktifleştirildi" if aktif else "devre dışı bırakıldı"
                messages.success(request, f'Hatırlatıcı başarıyla {status_text}.')
                return redirect('yks:hatirlatici_listesi')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': False,
            'message': 'Geçersiz istek.'
        }, status=400)
    else:
        messages.error(request, 'Geçersiz istek.')
        return redirect('yks:hatirlatici_listesi')


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
                ders=ders
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
                ders=ders
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