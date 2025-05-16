from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from .forms import KayitFormu, GirisFormu
from django.contrib.auth.models import User
from django.db.models import Count, Avg
import json
from datetime import datetime
from django.utils import timezone
from .models import SinavTurleri, SinavAltTur, Ders

def giris_view(request):
    """Kullanıcı girişi"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = GirisFormu(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Hoş geldiniz, {user.first_name}!")
                if user.is_staff or user.is_superuser:
                    return redirect('core:yetkili_panel')
                return redirect('index')
        else:
            messages.error(request, "Kullanıcı adı veya şifre hatalı.")
    else:
        form = GirisFormu()
    
    return render(request, 'core/giris.html', {'form': form})

def kayit_view(request):
    """Yeni kullanıcı kaydı"""
    if request.user.is_authenticated:
        return redirect('index')
        
    if request.method == 'POST':
        form = KayitFormu(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Hesabınız başarıyla oluşturuldu! Hoş geldiniz, {user.first_name}!")
            return redirect('index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = KayitFormu()
    
    return render(request, 'core/kayit.html', {'form': form})

def cikis_view(request):
    """Kullanıcı çıkışı"""
    logout(request)
    messages.success(request, "Başarıyla çıkış yaptınız.")
    return redirect('index')

# Yetkili personel kontrolü
def yetkili_kontrolu(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def yetkili_panel(request):
    """Yetkili kontrol paneli"""
    # İstatistiksel veriler
    kullanici_sayisi = User.objects.count()
    
    # YKS uygulaması varsa sınav istatistiklerini çekelim
    aktif_sinav_sayisi = 0
    tamamlanan_sinav_sayisi = 0
    ortalama_basari = 70  # Örnek değer
    
    try:
        from yks.models import YKSOturum
        # YKS oturum sayısını alalım (basit bir örnek)
        aktif_sinav_sayisi = YKSOturum.objects.count()
    except:
        # YKS uygulaması yüklü değilse veya başka bir hata olursa
        pass
    
    context = {
        'kullanici_sayisi': kullanici_sayisi,
        'aktif_sinav_sayisi': aktif_sinav_sayisi,
        'tamamlanan_sinav_sayisi': tamamlanan_sinav_sayisi,
        'ortalama_basari': ortalama_basari,
    }
    
    return render(request, 'core/yetkili_panel.html', context)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def oturumlar_view(request):
    """Sınav oturumları sayfası - tüm sınav türlerini gösterir"""
    # Aktif sınav türlerini getir
    sinav_turleri = SinavTurleri.objects.filter(aktif=True)
    
    context = {
        'sinav_turleri': sinav_turleri,
    }
    
    return render(request, 'core/yetkili_oturumlar.html', context)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def oturum_ekle(request):
    """Yeni sınav oturumu ekleme sayfası"""
    # Sınav türleri ve alt türleri (YKS için örnekler)
    sinav_turleri = {
        'YKS': ['TYT', 'AYT', 'YDT'],
    }
    
    if request.method == 'POST':
        sinav_turu = request.POST.get('sinav_turu')
        alt_tur = request.POST.get('alt_tur')
        tarih = request.POST.get('tarih')
        saat = request.POST.get('saat')
        
        try:
            # YKS oturumu ekleyelim
            if sinav_turu == 'YKS':
                from yks.models import YKSOturum
                
                # Alt türe göre isim ve kod belirle
                if alt_tur == 'TYT':
                    ad = "Temel Yeterlilik Testi"
                    kod = "TYT"
                    aciklama = "Türkçe, matematik, fen bilimleri ve sosyal bilimler testlerinden oluşan, üniversite sınavının ilk oturumudur."
                elif alt_tur == 'AYT':
                    ad = "Alan Yeterlilik Testi"
                    kod = "AYT"
                    aciklama = "Matematik, fen bilimleri, Türk dili ve edebiyatı-sosyal bilimler testlerinden oluşan oturumdur."
                elif alt_tur == 'YDT':
                    ad = "Yabancı Dil Testi"
                    kod = "YDT"
                    aciklama = "İngilizce, Almanca, Fransızca, Rusça veya Arapça dillerinden birinde yapılan oturumdur."
                else:
                    raise ValueError("Geçersiz alt tür")
                
                # Tarih ve saat bilgisini birleştir
                sinav_datetime = None
                sinav_yili = None
                if tarih and saat:
                    try:
                        sinav_datetime = datetime.strptime(f"{tarih} {saat}", "%Y-%m-%d %H:%M")
                        # Timezone bilgisi ekleyelim
                        sinav_datetime = timezone.make_aware(sinav_datetime)
                        sinav_yili = sinav_datetime.year
                    except:
                        raise ValueError("Tarih ve saat formatı geçersiz")
                else:
                    raise ValueError("Tarih ve saat bilgisi gereklidir")
                
                # Kullanıcı tarafından seçilen durum
                durum = request.POST.get('durum', YKSOturum.DURUM_BEKLIYOR)
                
                # Eğer aynı kodla ve yılla daha önce kayıt yapılmışsa update edelim
                oturum_exists = YKSOturum.objects.filter(kod=kod, yil=sinav_yili).exists()
                if oturum_exists:
                    return JsonResponse({
                        'success': False,
                        'message': f"{sinav_yili} yılına ait {kod} sınavı zaten veritabanında kayıtlı!"
                    })
                
                # Yeni kayıt oluştur
                oturum = YKSOturum.objects.create(
                    kod=kod,
                    yil=sinav_yili,
                    ad=ad,
                    aciklama=aciklama,
                    sinav_tarihi=sinav_datetime,
                    durum=durum
                )
                
                return JsonResponse({
                    'success': True, 
                    'message': f"{sinav_turu} {alt_tur} {sinav_yili} oturumu başarıyla kaydedildi!"
                })
            else:
                raise ValueError("Şu anda sadece YKS sınavları desteklenmektedir.")
                
        except Exception as e:
            return JsonResponse({
                'success': False, 
                'message': f"Hata oluştu: {str(e)}"
            })
    
    context = {
        'sinav_turleri': json.dumps(sinav_turleri),
    }
    
    return render(request, 'core/yetkili_oturum_ekle.html', context)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def sinav_alt_turler_api(request, sinav_turu_id):
    """Alt türleri getirmek için API endpoint"""
    sinav_turu = get_object_or_404(SinavTurleri, id=sinav_turu_id)
    alt_turler = SinavAltTur.objects.filter(sinav_turu=sinav_turu, aktif=True)
    
    # JSON formatına dönüştür
    alt_turler_json = []
    for alt_tur in alt_turler:
        alt_turler_json.append({
            'id': alt_tur.id,
            'ad': alt_tur.ad,
            'kod': alt_tur.kod,
            'aciklama': alt_tur.aciklama,
            'ikon': alt_tur.ikon
        })
    
    return JsonResponse(alt_turler_json, safe=False)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def oturum_detay(request, sinav_kodu, alt_tur_kodu=None):
    """Sınav türü veya alt tür detay sayfası"""
    sinav_turu = get_object_or_404(SinavTurleri, kod__iexact=sinav_kodu)
    
    if alt_tur_kodu:
        alt_tur = get_object_or_404(SinavAltTur, sinav_turu=sinav_turu, kod__iexact=alt_tur_kodu)
        context = {
            'sinav_turu': sinav_turu,
            'alt_tur': alt_tur
        }
        return render(request, 'core/yetkili_oturum_alt_tur_detay.html', context)
    else:
        context = {
            'sinav_turu': sinav_turu
        }
        return render(request, 'core/yetkili_oturum_detay.html', context)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def ders_ekle(request):
    """Ders ekleme API'si"""
    if request.method == 'POST':
        try:
            # Form verilerini al
            ad = request.POST.get('ad')
            kod = request.POST.get('kod')
            aciklama = request.POST.get('aciklama')
            ikon = request.POST.get('ikon')
            alt_tur_id = request.POST.get('alt_tur_id')
            sinav_turu_id = request.POST.get('sinav_turu_id')
            
            # Validasyon
            if not ad or not kod:
                return JsonResponse({'success': False, 'message': 'Ders adı ve kod alanları zorunludur.'})
            
            # Alt tür veya sınav türü kontrol et
            if alt_tur_id:
                alt_tur = get_object_or_404(SinavAltTur, id=alt_tur_id)
                sinav_turu = alt_tur.sinav_turu  # Alt türün bağlı olduğu sınav türünü al
            elif sinav_turu_id:
                sinav_turu = get_object_or_404(SinavTurleri, id=sinav_turu_id)
                alt_tur = None
            else:
                return JsonResponse({'success': False, 'message': 'Sınav türü veya alt tür belirtilmelidir.'})
            
            # Aynı koda sahip ders var mı kontrol et
            if alt_tur and Ders.objects.filter(alt_tur=alt_tur, kod=kod).exists():
                return JsonResponse({'success': False, 'message': f'"{kod}" kodlu ders bu alt türde zaten mevcut.'})
            
            # Ders oluştur
            ders = Ders.objects.create(
                ad=ad,
                kod=kod,
                aciklama=aciklama,
                ikon=ikon if ikon else None,
                alt_tur=alt_tur,
                sinav_turu=sinav_turu,
                aktif=True
            )
            
            return JsonResponse({
                'success': True,
                'message': f'"{ad}" dersi başarıyla eklendi.',
                'ders': {
                    'id': ders.id,
                    'ad': ders.ad,
                    'kod': ders.kod,
                    'aciklama': ders.aciklama,
                    'ikon': ders.ikon,
                    'aktif': ders.aktif
                }
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'Hata oluştu: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'Geçersiz istek yöntemi.'})


