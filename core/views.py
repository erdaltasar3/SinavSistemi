from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count, Avg, Q
import json
from .forms import (
    KayitFormu, GirisFormu, UserProfileForm,
    DersForm, UniteForm, KonuForm
)
from django.contrib.auth.models import User
from .models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu
)
from datetime import timedelta, date, datetime

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

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def ders_duzenle(request, ders_id):
    """Ders düzenleme sayfası - üniteler ve konular eklemek için"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders).order_by('sira_no')
    
    # Tüm ünitelere ait konuları getir
    unite_konular = {}
    for unite in uniteler:
        konular = Konu.objects.filter(unite=unite).order_by('sira_no')
        unite_konular[unite.id] = konular
    
    context = {
        'ders': ders,
        'uniteler': uniteler,
        'unite_konular': unite_konular,
    }
    
    return render(request, 'core/ders_duzenle.html', context)

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def unite_ekle(request):
    """Yeni ünite eklemek için API endpoint"""
    if request.method == 'POST':
        try:
            ders_id = request.POST.get('ders_id')
            ad = request.POST.get('ad')
            sira_no = request.POST.get('sira_no', 1)
            aciklama = request.POST.get('aciklama', '')
            
            ders = get_object_or_404(Ders, id=ders_id)
            
            # En son ünite sıra numarasını kontrol et
            son_unite = Unite.objects.filter(ders=ders).order_by('-sira_no').first()
            if son_unite and not sira_no:
                sira_no = son_unite.sira_no + 1
            
            unite = Unite.objects.create(
                ders=ders,
                ad=ad,
                sira_no=sira_no,
                aciklama=aciklama,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Ünite başarıyla eklendi.',
                'unite': {
                    'id': unite.id,
                    'ad': unite.ad,
                    'sira_no': unite.sira_no,
                    'aciklama': unite.aciklama,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def unite_duzenle(request, unite_id):
    """Ünite düzenlemek için API endpoint"""
    unite = get_object_or_404(Unite, id=unite_id)
    
    if request.method == 'POST':
        try:
            unite.ad = request.POST.get('ad', unite.ad)
            unite.sira_no = request.POST.get('sira_no', unite.sira_no)
            unite.aciklama = request.POST.get('aciklama', unite.aciklama)
            unite.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Ünite başarıyla güncellendi.',
                'unite': {
                    'id': unite.id,
                    'ad': unite.ad,
                    'sira_no': unite.sira_no,
                    'aciklama': unite.aciklama,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    # GET isteği için ünite bilgilerini döndür
    return JsonResponse({
        'success': True,
        'unite': {
            'id': unite.id,
            'ad': unite.ad,
            'sira_no': unite.sira_no,
            'aciklama': unite.aciklama,
        }
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def unite_sil(request, unite_id):
    """Ünite silmek için API endpoint"""
    if request.method == 'POST':
        try:
            unite = get_object_or_404(Unite, id=unite_id)
            unite_ad = unite.ad
            unite.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'"{unite_ad}" ünitesi başarıyla silindi.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def konu_ekle(request):
    """Yeni konu eklemek için API endpoint"""
    if request.method == 'POST':
        try:
            unite_id = request.POST.get('unite_id')
            ad = request.POST.get('ad')
            sira_no = request.POST.get('sira_no', 1)
            aciklama = request.POST.get('aciklama', '')
            
            unite = get_object_or_404(Unite, id=unite_id)
            
            # En son konu sıra numarasını kontrol et
            son_konu = Konu.objects.filter(unite=unite).order_by('-sira_no').first()
            if son_konu and not sira_no:
                sira_no = son_konu.sira_no + 1
            
            konu = Konu.objects.create(
                unite=unite,
                ad=ad,
                sira_no=sira_no,
                aciklama=aciklama,
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Konu başarıyla eklendi.',
                'konu': {
                    'id': konu.id,
                    'ad': konu.ad,
                    'sira_no': konu.sira_no,
                    'aciklama': konu.aciklama,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def konu_duzenle(request, konu_id):
    """Konu düzenlemek için API endpoint"""
    konu = get_object_or_404(Konu, id=konu_id)
    
    if request.method == 'POST':
        try:
            konu.ad = request.POST.get('ad', konu.ad)
            konu.sira_no = request.POST.get('sira_no', konu.sira_no)
            konu.aciklama = request.POST.get('aciklama', konu.aciklama)
            konu.save()
            
            return JsonResponse({
                'success': True,
                'message': 'Konu başarıyla güncellendi.',
                'konu': {
                    'id': konu.id,
                    'ad': konu.ad,
                    'sira_no': konu.sira_no,
                    'aciklama': konu.aciklama,
                }
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    # GET isteği için konu bilgilerini döndür
    return JsonResponse({
        'success': True,
        'konu': {
            'id': konu.id,
            'ad': konu.ad,
            'sira_no': konu.sira_no,
            'aciklama': konu.aciklama,
        }
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def konu_sil(request, konu_id):
    """Konu silmek için API endpoint"""
    if request.method == 'POST':
        try:
            konu = get_object_or_404(Konu, id=konu_id)
            konu_ad = konu.ad
            konu.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'"{konu_ad}" konusu başarıyla silindi.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def ders_sil(request, ders_id):
    """Ders silmek için API endpoint"""
    if request.method == 'POST':
        try:
            ders = get_object_or_404(Ders, id=ders_id)
            ders_ad = ders.ad
            ders.delete()
            
            return JsonResponse({
                'success': True,
                'message': f'"{ders_ad}" dersi başarıyla silindi.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Hata oluştu: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Geçersiz istek.'
    })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def unite_konular_son_sira_api(request, unite_id):
    """Bir üniteye ait konuların son sıra numarasını getirmek için API endpoint"""
    try:
        unite = get_object_or_404(Unite, id=unite_id)
        # Son konu varsa sıra numarasını al ve bir arttır
        son_konu = Konu.objects.filter(unite=unite).order_by('-sira_no').first()
        next_sira_no = 1  # Varsayılan değer
        
        if son_konu:
            next_sira_no = son_konu.sira_no + 1
            
        return JsonResponse({
            'success': True,
            'next_sira_no': next_sira_no
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        })

@login_required
@user_passes_test(yetkili_kontrolu, login_url='core:giris')
def ders_uniteler_son_sira_api(request, ders_id):
    """Bir derse ait ünitelerin son sıra numarasını getirmek için API endpoint"""
    try:
        ders = get_object_or_404(Ders, id=ders_id)
        # Son ünite varsa sıra numarasını al ve bir artır
        son_unite = Unite.objects.filter(ders=ders).order_by('-sira_no').first()
        next_sira_no = 1  # Varsayılan değer
        
        if son_unite:
            next_sira_no = son_unite.sira_no + 1
            
        return JsonResponse({
            'success': True,
            'next_sira_no': next_sira_no
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Hata oluştu: {str(e)}'
        })

# Hedef Belirleme ve Takip view fonksiyonları

"""
# Hedefler ile ilgili görünümler devre dışı bırakıldı
@login_required
def hedef_listesi(request):
    # Hedef listesi görünümü
    hedefler = CalismaHedefi.objects.filter(kullanici=request.user).order_by('-olusturulma_tarihi')
    
    # Duruma göre filtreleme
    aktif_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_AKTIF)
    tamamlanan_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_TAMAMLANDI)
    iptal_edilen_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_IPTAL)
    
    context = {
        'aktif_hedefler': aktif_hedefler,
        'tamamlanan_hedefler': tamamlanan_hedefler,
        'iptal_edilen_hedefler': iptal_edilen_hedefler
    }
    
    return render(request, 'core/hedefler/hedef_listesi.html', context)

@login_required
def hedef_ekle(request):
    # Hedef ekleme görünümü
    if request.method == 'POST':
        form = CalismaHedefiForm(request.POST)
        if form.is_valid():
            hedef = form.save(commit=False)
            hedef.kullanici = request.user
            hedef.save()
            messages.success(request, 'Hedef başarıyla oluşturuldu.')
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaHedefiForm()
    
    return render(request, 'core/hedefler/hedef_form.html', {'form': form, 'baslik': 'Yeni Hedef'})

@login_required
def hedef_detay(request, hedef_id):
    # Hedef detay görünümü
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Sadece hedef sahibi görebilir
    if hedef.kullanici != request.user:
        raise PermissionDenied
    
    # Hedefle ilgili planları getir
    planlar = CalismaPlani.objects.filter(hedef=hedef).order_by('planlanan_tarih')
    
    # Planların durumlarına göre istatistikler
    tamamlanan_planlar = planlar.filter(durum=CalismaPlani.DURUM_TAMAMLANDI).count()
    toplam_plan = planlar.count()
    tamamlanma_orani = 0
    if toplam_plan > 0:
        tamamlanma_orani = (tamamlanan_planlar / toplam_plan) * 100
    
    context = {
        'hedef': hedef,
        'planlar': planlar,
        'tamamlanan_planlar': tamamlanan_planlar,
        'toplam_plan': toplam_plan,
        'tamamlanma_orani': tamamlanma_orani
    }
    
    return render(request, 'core/hedefler/hedef_detay.html', context)

@login_required
def hedef_duzenle(request, hedef_id):
    # Hedef düzenleme görünümü
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Sadece hedef sahibi düzenleyebilir
    if hedef.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CalismaHedefiForm(request.POST, instance=hedef)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hedef başarıyla güncellendi.')
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaHedefiForm(instance=hedef)
    
    return render(request, 'core/hedefler/hedef_form.html', {'form': form, 'baslik': 'Hedef Düzenle'})

@login_required
def hedef_sil(request, hedef_id):
    # Hedef silme görünümü (durum iptal olarak değiştirilecek)
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Sadece hedef sahibi silebilir
    if hedef.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        # Hedefi iptal et
        hedef.durum = CalismaHedefi.DURUM_IPTAL
        hedef.save()
        messages.success(request, 'Hedef iptal edildi.')
        return redirect('core:hedef_listesi')
    
    return render(request, 'core/hedefler/hedef_sil.html', {'hedef': hedef})

@login_required
def plan_ekle(request, hedef_id):
    # Plan ekleme görünümü
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Sadece hedef sahibi plan ekleyebilir
    if hedef.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CalismaPlaniForm(request.POST, user=request.user, hedef_id=hedef_id)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.hedef = hedef
            plan.save()
            messages.success(request, 'Plan başarıyla oluşturuldu.')
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaPlaniForm(user=request.user, hedef_id=hedef_id)
    
    return render(request, 'core/planlar/plan_form.html', {'form': form, 'baslik': 'Yeni Plan', 'hedef': hedef})

@login_required
def plan_detay(request, plan_id):
    # Plan detay görünümü
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Sadece plan sahibi görebilir
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied
    
    return render(request, 'core/planlar/plan_detay.html', {'plan': plan})

@login_required
def plan_duzenle(request, plan_id):
    # Plan düzenleme görünümü
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Sadece plan sahibi düzenleyebilir
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CalismaPlaniForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan başarıyla güncellendi.')
            return redirect('core:plan_detay', plan_id=plan.id)
    else:
        form = CalismaPlaniForm(instance=plan, user=request.user)
    
    return render(request, 'core/planlar/plan_form.html', {
        'form': form, 
        'baslik': 'Plan Düzenle',
        'hedef': plan.hedef
    })

@login_required
def plan_sil(request, plan_id):
    # Plan silme görünümü
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Sadece plan sahibi silebilir
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied
    
    hedef_id = plan.hedef.id
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Plan silindi.')
        return redirect('core:hedef_detay', hedef_id=hedef_id)
    
    return render(request, 'core/planlar/plan_sil.html', {'plan': plan})

@login_required
def plan_tamamla(request, plan_id):
    # Plan tamamlama görünümü
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Sadece plan sahibi tamamlayabilir
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = PlanTamamlamaForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, 'Plan tamamlandı.')
            return redirect('core:hedef_detay', hedef_id=plan.hedef.id)
    else:
        form = PlanTamamlamaForm(instance=plan)
    
    return render(request, 'core/planlar/plan_tamamla.html', {'form': form, 'plan': plan})

@login_required
def hatirlatici_listesi(request):
    # Hatırlatıcı listesi görünümü
    hatirlaticilar = Hatirlatici.objects.filter(kullanici=request.user).order_by('tarih', 'saat')
    
    # Bugünkü, gelecek ve geçmiş hatırlatıcılar
    bugun = timezone.now().date()
    bugunku_hatirlaticilar = hatirlaticilar.filter(tarih=bugun)
    gelecek_hatirlaticilar = hatirlaticilar.filter(tarih__gt=bugun)
    gecmis_hatirlaticilar = hatirlaticilar.filter(tarih__lt=bugun)
    
    # Duruma göre filtreleme
    aktif_hatirlaticilar = hatirlaticilar.filter(durum=Hatirlatici.DURUM_AKTIF)
    tamamlanan_hatirlaticilar = hatirlaticilar.filter(durum=Hatirlatici.DURUM_TAMAMLANDI)
    
    context = {
        'bugunku_hatirlaticilar': bugunku_hatirlaticilar,
        'gelecek_hatirlaticilar': gelecek_hatirlaticilar,
        'gecmis_hatirlaticilar': gecmis_hatirlaticilar,
        'aktif_hatirlaticilar': aktif_hatirlaticilar,
        'tamamlanan_hatirlaticilar': tamamlanan_hatirlaticilar
    }
    
    return render(request, 'core/hatirlaticilar/hatirlatici_listesi.html', context)

@login_required
def hatirlatici_ekle(request):
    # Hatırlatıcı ekleme görünümü
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST)
        if form.is_valid():
            hatirlatici = form.save(commit=False)
            hatirlatici.kullanici = request.user
            hatirlatici.save()
            messages.success(request, 'Hatırlatıcı başarıyla oluşturuldu.')
            return redirect('core:hatirlatici_listesi')
    else:
        form = HatirlaticiForm()
    
    return render(request, 'core/hatirlaticilar/hatirlatici_form.html', {'form': form, 'baslik': 'Yeni Hatırlatıcı'})

@login_required
def hatirlatici_detay(request, hatirlatici_id):
    # Hatırlatıcı detay görünümü
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Sadece hatırlatıcı sahibi görebilir
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied
    
    return render(request, 'core/hatirlaticilar/hatirlatici_detay.html', {'hatirlatici': hatirlatici})

@login_required
def hatirlatici_duzenle(request, hatirlatici_id):
    # Hatırlatıcı düzenleme görünümü
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Sadece hatırlatıcı sahibi düzenleyebilir
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST, instance=hatirlatici)
        if form.is_valid():
            form.save()
            messages.success(request, 'Hatırlatıcı başarıyla güncellendi.')
            return redirect('core:hatirlatici_detay', hatirlatici_id=hatirlatici.id)
    else:
        form = HatirlaticiForm(instance=hatirlatici)
    
    return render(request, 'core/hatirlaticilar/hatirlatici_form.html', {'form': form, 'baslik': 'Hatırlatıcı Düzenle'})

@login_required
def hatirlatici_sil(request, hatirlatici_id):
    # Hatırlatıcı silme görünümü
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Sadece hatırlatıcı sahibi silebilir
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        hatirlatici.delete()
        messages.success(request, 'Hatırlatıcı silindi.')
        return redirect('core:hatirlatici_listesi')
    
    return render(request, 'core/hatirlaticilar/hatirlatici_sil.html', {'hatirlatici': hatirlatici})

@login_required
def hatirlatici_tamamla(request, hatirlatici_id):
    # Hatırlatıcı tamamlama görünümü
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Sadece hatırlatıcı sahibi tamamlayabilir
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        # Hatırlatıcıyı tamamlandı olarak işaretle
        hatirlatici.durum = Hatirlatici.DURUM_TAMAMLANDI
        hatirlatici.save()
        messages.success(request, 'Hatırlatıcı tamamlandı olarak işaretlendi.')
        return redirect('core:hatirlatici_listesi')
    
    return render(request, 'core/hatirlaticilar/hatirlatici_sil.html', {
        'hatirlatici': hatirlatici,
        'baslik': 'Hatırlatıcıyı Tamamla',
        'mesaj': 'Bu hatırlatıcıyı tamamlandı olarak işaretlemek istediğinize emin misiniz?'
    })

@login_required
def yapilacak_listesi(request):
    # Yapılacaklar listesi görünümü
    yapilacaklar = YapilacakListesi.objects.filter(kullanici=request.user).order_by('son_tarih')
    
    # Bugün, gelecek ve geçmiş yapılacaklar
    bugun = timezone.now().date()
    bugunku_yapilacaklar = yapilacaklar.filter(son_tarih=bugun)
    gelecek_yapilacaklar = yapilacaklar.filter(son_tarih__gt=bugun)
    gecmis_yapilacaklar = yapilacaklar.filter(son_tarih__lt=bugun, son_tarih__isnull=False)
    tarihi_olmayanlar = yapilacaklar.filter(son_tarih__isnull=True)
    
    # Duruma göre filtreleme
    aktif_yapilacaklar = yapilacaklar.filter(durum=YapilacakListesi.DURUM_AKTIF)
    tamamlanan_yapilacaklar = yapilacaklar.filter(durum=YapilacakListesi.DURUM_TAMAMLANDI)
    
    context = {
        'bugunku_yapilacaklar': bugunku_yapilacaklar,
        'gelecek_yapilacaklar': gelecek_yapilacaklar,
        'gecmis_yapilacaklar': gecmis_yapilacaklar,
        'tarihi_olmayanlar': tarihi_olmayanlar,
        'aktif_yapilacaklar': aktif_yapilacaklar,
        'tamamlanan_yapilacaklar': tamamlanan_yapilacaklar
    }
    
    return render(request, 'core/yapilacaklar/yapilacak_listesi.html', context)

@login_required
def yapilacak_ekle(request):
    # Yapılacak ekleme görünümü
    if request.method == 'POST':
        form = YapilacakListesiForm(request.POST)
        if form.is_valid():
            yapilacak = form.save(commit=False)
            yapilacak.kullanici = request.user
            yapilacak.save()
            messages.success(request, 'Yapılacak görev başarıyla oluşturuldu.')
            return redirect('core:yapilacak_listesi')
    else:
        form = YapilacakListesiForm()
    
    return render(request, 'core/yapilacaklar/yapilacak_form.html', {'form': form, 'baslik': 'Yeni Görev'})

@login_required
def yapilacak_detay(request, yapilacak_id):
    # Yapılacak detay görünümü
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Sadece görev sahibi görebilir
    if yapilacak.kullanici != request.user:
        raise PermissionDenied
    
    return render(request, 'core/yapilacaklar/yapilacak_detay.html', {'yapilacak': yapilacak})

@login_required
def yapilacak_duzenle(request, yapilacak_id):
    # Yapılacak düzenleme görünümü
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Sadece görev sahibi düzenleyebilir
    if yapilacak.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        form = YapilacakListesiForm(request.POST, instance=yapilacak)
        if form.is_valid():
            form.save()
            messages.success(request, 'Görev başarıyla güncellendi.')
            return redirect('core:yapilacak_detay', yapilacak_id=yapilacak.id)
    else:
        form = YapilacakListesiForm(instance=yapilacak)
    
    return render(request, 'core/yapilacaklar/yapilacak_form.html', {'form': form, 'baslik': 'Görev Düzenle'})

@login_required
def yapilacak_sil(request, yapilacak_id):
    # Yapılacak silme görünümü
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Sadece görev sahibi silebilir
    if yapilacak.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        yapilacak.delete()
        messages.success(request, 'Görev silindi.')
        return redirect('core:yapilacak_listesi')
    
    return render(request, 'core/yapilacaklar/yapilacak_sil.html', {'yapilacak': yapilacak})

@login_required
def yapilacak_tamamla(request, yapilacak_id):
    # Yapılacak tamamlama görünümü
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Sadece görev sahibi tamamlayabilir
    if yapilacak.kullanici != request.user:
        raise PermissionDenied
    
    if request.method == 'POST':
        # Görevi tamamlandı olarak işaretle
        yapilacak.durum = YapilacakListesi.DURUM_TAMAMLANDI
        yapilacak.tamamlanma_tarihi = timezone.now()
        yapilacak.save()
        messages.success(request, 'Görev tamamlandı olarak işaretlendi.')
        return redirect('core:yapilacak_listesi')
    
    return render(request, 'core/yapilacaklar/yapilacak_sil.html', {
        'yapilacak': yapilacak,
        'baslik': 'Görevi Tamamla',
        'mesaj': 'Bu görevi tamamlandı olarak işaretlemek istediğinize emin misiniz?'
    })
"""

# Hata sayfaları
def hata_403(request, exception=None):
    """403 Hata Sayfası"""
    return render(request, 'core/hatalar/403.html', status=403)

def hata_404(request, exception=None):
    """404 Hata Sayfası"""
    return render(request, 'core/hatalar/404.html', status=404)

def hata_500(request):
    """500 Hata Sayfası"""
    return render(request, 'core/hatalar/500.html', status=500)

# Create your views here.
def index(request):
    """Ana sayfa görünümü"""
    # Kullanıcı oturum açmışsa
    if request.user.is_authenticated:
        # Sınav türlerini getir
        sinav_turleri = SinavTurleri.objects.filter(aktif=True)
        
        context = {
            'sinav_turleri': sinav_turleri
        }
        
        return render(request, 'core/index.html', context)
    
    # Oturum açmamışsa
    return render(request, 'core/index.html')

# Ders, Ünite ve Konu modülleri için görünümler
@login_required
def ders_listesi(request):
    """Ders listesi görünümü"""
    dersler = Ders.objects.filter(aktif=True)
    
    context = {
        'dersler': dersler
    }
    
    return render(request, 'core/dersler/ders_listesi.html', context)

@login_required
def ders_detay(request, ders_id):
    """Ders detay görünümü"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders, aktif=True)
    
    # Her ünite için konu sayısını al
    for unite in uniteler:
        unite.konu_sayisi = Konu.objects.filter(unite=unite, aktif=True).count()
    
    context = {
        'ders': ders,
        'uniteler': uniteler
    }
    
    return render(request, 'core/dersler/ders_detay.html', context)

@login_required
def unite_listesi(request, ders_id):
    """Ünite listesi görünümü"""
    ders = get_object_or_404(Ders, id=ders_id)
    uniteler = Unite.objects.filter(ders=ders, aktif=True)
    
    context = {
        'ders': ders,
        'uniteler': uniteler
    }
    
    return render(request, 'core/uniteler/unite_listesi.html', context)

@login_required
def unite_detay(request, unite_id):
    """Ünite detay görünümü"""
    unite = get_object_or_404(Unite, id=unite_id)
    konular = Konu.objects.filter(unite=unite, aktif=True)
    
    context = {
        'unite': unite,
        'konular': konular
    }
    
    return render(request, 'core/uniteler/unite_detay.html', context)

@login_required
def konu_listesi(request, unite_id):
    """Konu listesi görünümü"""
    unite = get_object_or_404(Unite, id=unite_id)
    konular = Konu.objects.filter(unite=unite, aktif=True)
    
    context = {
        'unite': unite,
        'konular': konular
    }
    
    return render(request, 'core/konular/konu_listesi.html', context)

@login_required
def konu_detay(request, konu_id):
    """Konu detay görünümü"""
    konu = get_object_or_404(Konu, id=konu_id)
    
    context = {
        'konu': konu
    }
    
    return render(request, 'core/konular/konu_detay.html', context)

@login_required
def profile_view(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
            return redirect('core:profile')
    else:
        form = UserProfileForm(instance=user_profile)

    context = {
        'form': form
    }
    return render(request, 'core/profile.html', context)


