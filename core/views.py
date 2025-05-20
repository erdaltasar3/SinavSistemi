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
    KayitFormu, GirisFormu, 
    CalismaHedefiForm, CalismaPlaniForm, HatirlaticiForm, YapilacakListesiForm, PlanTamamlamaForm
)
from django.contrib.auth.models import User
from .models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu,
    CalismaHedefi, CalismaPlani, Hatirlatici, YapilacakListesi
)

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

@login_required
def hedef_listesi(request):
    """Kullanıcının çalışma hedeflerini listeler"""
    hedefler = CalismaHedefi.objects.filter(kullanici=request.user).order_by('-olusturulma_tarihi')
    
    # Aktif, tamamlanan ve iptal edilen hedefleri ayır
    aktif_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_AKTIF)
    tamamlanan_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_TAMAMLANDI)
    iptal_edilen_hedefler = hedefler.filter(durum=CalismaHedefi.DURUM_IPTAL)
    
    context = {
        'aktif_hedefler': aktif_hedefler,
        'tamamlanan_hedefler': tamamlanan_hedefler,
        'iptal_edilen_hedefler': iptal_edilen_hedefler,
    }
    return render(request, 'core/hedefler/hedef_listesi.html', context)

@login_required
def hedef_ekle(request):
    """Yeni çalışma hedefi ekleme"""
    if request.method == 'POST':
        form = CalismaHedefiForm(request.POST)
        if form.is_valid():
            hedef = form.save(commit=False)
            hedef.kullanici = request.user
            hedef.save()
            messages.success(request, "Yeni hedef başarıyla oluşturuldu.")
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaHedefiForm()
    
    return render(request, 'core/hedefler/hedef_form.html', {'form': form, 'baslik': 'Yeni Hedef Ekle'})

@login_required
def hedef_detay(request, hedef_id):
    """Çalışma hedefi detayları ve ilişkili çalışma planları"""
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Yetki kontrolü
    if hedef.kullanici != request.user:
        raise PermissionDenied("Bu hedefi görüntüleme yetkiniz yok.")
    
    # Hedefin çalışma planlarını al
    planlar = hedef.calisma_planlari.all().order_by('planlanan_tarih')
    
    # Durum ve tarihe göre planları ayır
    bugun = timezone.now().date()
    
    bekleyen_planlar = planlar.filter(durum=CalismaPlani.DURUM_BEKLIYOR)
    gecmis_planlar = bekleyen_planlar.filter(planlanan_tarih__lt=bugun)
    bugunun_planlari = bekleyen_planlar.filter(planlanan_tarih=bugun)
    gelecek_planlar = bekleyen_planlar.filter(planlanan_tarih__gt=bugun)
    tamamlanan_planlar = planlar.filter(durum=CalismaPlani.DURUM_TAMAMLANDI)
    iptal_edilen_planlar = planlar.filter(durum=CalismaPlani.DURUM_IPTAL)
    
    context = {
        'hedef': hedef,
        'gecmis_planlar': gecmis_planlar,
        'bugunun_planlari': bugunun_planlari,
        'gelecek_planlar': gelecek_planlar,
        'tamamlanan_planlar': tamamlanan_planlar,
        'iptal_edilen_planlar': iptal_edilen_planlar,
    }
    return render(request, 'core/hedefler/hedef_detay.html', context)

@login_required
def hedef_duzenle(request, hedef_id):
    """Çalışma hedefi düzenleme"""
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Yetki kontrolü
    if hedef.kullanici != request.user:
        raise PermissionDenied("Bu hedefi düzenleme yetkiniz yok.")
    
    if request.method == 'POST':
        form = CalismaHedefiForm(request.POST, instance=hedef)
        if form.is_valid():
            form.save()
            messages.success(request, "Hedef başarıyla güncellendi.")
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaHedefiForm(instance=hedef)
    
    return render(request, 'core/hedefler/hedef_form.html', 
                 {'form': form, 'baslik': 'Hedef Düzenle', 'hedef': hedef})

@login_required
def hedef_sil(request, hedef_id):
    """Çalışma hedefi silme"""
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Yetki kontrolü
    if hedef.kullanici != request.user:
        raise PermissionDenied("Bu hedefi silme yetkiniz yok.")
    
    if request.method == 'POST':
        # Hedefi iptal et (silme yerine durumunu güncelle)
        hedef.durum = CalismaHedefi.DURUM_IPTAL
        hedef.save()
        messages.success(request, "Hedef iptal edildi.")
        return redirect('core:hedef_listesi')
    
    return render(request, 'core/hedefler/hedef_sil.html', {'hedef': hedef})

@login_required
def plan_ekle(request, hedef_id):
    """Çalışma planı ekleme"""
    hedef = get_object_or_404(CalismaHedefi, id=hedef_id)
    
    # Yetki kontrolü
    if hedef.kullanici != request.user:
        raise PermissionDenied("Bu hedefe plan ekleme yetkiniz yok.")
    
    if request.method == 'POST':
        form = CalismaPlaniForm(request.POST, user=request.user, hedef_id=hedef_id)
        if form.is_valid():
            plan = form.save(commit=False)
            # Formda hedef alanı varsa, otomatik olarak atanır
            if not hasattr(plan, 'hedef') or not plan.hedef:
                plan.hedef = hedef
            plan.save()
            messages.success(request, "Çalışma planı başarıyla oluşturuldu.")
            return redirect('core:hedef_detay', hedef_id=hedef.id)
    else:
        form = CalismaPlaniForm(user=request.user, hedef_id=hedef_id)
    
    # Dersler ve konular için veri hazırla (JavaScript ile dinamik olarak doldurulacak)
    dersler = Ders.objects.filter(aktif=True)
    
    return render(request, 'core/planlar/plan_form.html', {
        'form': form, 
        'baslik': 'Yeni Çalışma Planı', 
        'hedef': hedef,
        'dersler': dersler,
    })

@login_required
def plan_detay(request, plan_id):
    """Çalışma planı detayları"""
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Yetki kontrolü
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied("Bu planı görüntüleme yetkiniz yok.")
    
    return render(request, 'core/planlar/plan_detay.html', {'plan': plan})

@login_required
def plan_duzenle(request, plan_id):
    """Çalışma planı düzenleme"""
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Yetki kontrolü
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied("Bu planı düzenleme yetkiniz yok.")
    
    if request.method == 'POST':
        form = CalismaPlaniForm(request.POST, instance=plan, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Çalışma planı başarıyla güncellendi.")
            return redirect('core:plan_detay', plan_id=plan.id)
    else:
        form = CalismaPlaniForm(instance=plan, user=request.user)
    
    # Dersler ve konular için veri hazırla
    dersler = Ders.objects.filter(aktif=True)
    
    return render(request, 'core/planlar/plan_form.html', {
        'form': form, 
        'baslik': 'Çalışma Planı Düzenle', 
        'plan': plan,
        'hedef': plan.hedef,
        'dersler': dersler,
    })

@login_required
def plan_sil(request, plan_id):
    """Çalışma planı silme"""
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Yetki kontrolü
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied("Bu planı silme yetkiniz yok.")
    
    hedef_id = plan.hedef.id
    
    if request.method == 'POST':
        # Planı iptal et (silme yerine durumunu güncelle)
        plan.durum = CalismaPlani.DURUM_IPTAL
        plan.save()
        messages.success(request, "Çalışma planı iptal edildi.")
        return redirect('core:hedef_detay', hedef_id=hedef_id)
    
    return render(request, 'core/planlar/plan_sil.html', {'plan': plan})

@login_required
def plan_tamamla(request, plan_id):
    """Çalışma planı tamamlama"""
    plan = get_object_or_404(CalismaPlani, id=plan_id)
    
    # Yetki kontrolü
    if plan.hedef.kullanici != request.user:
        raise PermissionDenied("Bu planı tamamlama yetkiniz yok.")
    
    if request.method == 'POST':
        form = PlanTamamlamaForm(request.POST, instance=plan)
        if form.is_valid():
            form.save()
            messages.success(request, "Çalışma planı durumu güncellendi.")
            return redirect('core:hedef_detay', hedef_id=plan.hedef.id)
    else:
        # Önceden gerceklesen_sure yoksa planlanan süreyi öner
        if plan.gerceklesen_sure == 0:
            plan.gerceklesen_sure = plan.planlanan_sure
        
        form = PlanTamamlamaForm(instance=plan)
    
    return render(request, 'core/planlar/plan_tamamla.html', {'form': form, 'plan': plan})

@login_required
def hatirlatici_listesi(request):
    """Kullanıcının hatırlatıcı listesi"""
    bugun = timezone.now().date()
    
    # Aktif hatırlatıcıları al
    aktif_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user, 
        durum=Hatirlatici.DURUM_AKTIF
    ).order_by('tarih', 'saat')
    
    # Tarihe göre grupla
    gecmis_hatirlaticilar = aktif_hatirlaticilar.filter(tarih__lt=bugun)
    bugunun_hatirlaticilari = aktif_hatirlaticilar.filter(tarih=bugun)
    gelecek_hatirlaticilar = aktif_hatirlaticilar.filter(tarih__gt=bugun)
    
    # Tamamlanan ve iptal edilen hatırlatıcılar
    tamamlanan_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user, 
        durum=Hatirlatici.DURUM_TAMAMLANDI
    ).order_by('-guncelleme_tarihi')
    
    iptal_edilen_hatirlaticilar = Hatirlatici.objects.filter(
        kullanici=request.user, 
        durum=Hatirlatici.DURUM_IPTAL
    ).order_by('-guncelleme_tarihi')
    
    context = {
        'gecmis_hatirlaticilar': gecmis_hatirlaticilar,
        'bugunun_hatirlaticilari': bugunun_hatirlaticilari,
        'gelecek_hatirlaticilar': gelecek_hatirlaticilar,
        'tamamlanan_hatirlaticilar': tamamlanan_hatirlaticilar,
        'iptal_edilen_hatirlaticilar': iptal_edilen_hatirlaticilar,
    }
    return render(request, 'core/hatirlaticilar/hatirlatici_listesi.html', context)

@login_required
def hatirlatici_ekle(request):
    """Yeni hatırlatıcı ekleme"""
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST)
        if form.is_valid():
            hatirlatici = form.save(commit=False)
            hatirlatici.kullanici = request.user
            hatirlatici.save()
            messages.success(request, "Hatırlatıcı başarıyla oluşturuldu.")
            return redirect('core:hatirlatici_listesi')
    else:
        form = HatirlaticiForm()
    
    return render(request, 'core/hatirlaticilar/hatirlatici_form.html', 
                 {'form': form, 'baslik': 'Yeni Hatırlatıcı Ekle'})

@login_required
def hatirlatici_detay(request, hatirlatici_id):
    """Hatırlatıcı detayları"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Yetki kontrolü
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied("Bu hatırlatıcıyı görüntüleme yetkiniz yok.")
    
    return render(request, 'core/hatirlaticilar/hatirlatici_detay.html', {'hatirlatici': hatirlatici})

@login_required
def hatirlatici_duzenle(request, hatirlatici_id):
    """Hatırlatıcı düzenleme"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Yetki kontrolü
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied("Bu hatırlatıcıyı düzenleme yetkiniz yok.")
    
    if request.method == 'POST':
        form = HatirlaticiForm(request.POST, instance=hatirlatici)
        if form.is_valid():
            form.save()
            messages.success(request, "Hatırlatıcı başarıyla güncellendi.")
            return redirect('core:hatirlatici_detay', hatirlatici_id=hatirlatici.id)
    else:
        form = HatirlaticiForm(instance=hatirlatici)
    
    return render(request, 'core/hatirlaticilar/hatirlatici_form.html', 
                 {'form': form, 'baslik': 'Hatırlatıcı Düzenle', 'hatirlatici': hatirlatici})

@login_required
def hatirlatici_sil(request, hatirlatici_id):
    """Hatırlatıcı silme"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Yetki kontrolü
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied("Bu hatırlatıcıyı silme yetkiniz yok.")
    
    if request.method == 'POST':
        # Hatırlatıcıyı iptal et (silme yerine durumunu güncelle)
        hatirlatici.durum = Hatirlatici.DURUM_IPTAL
        hatirlatici.save()
        messages.success(request, "Hatırlatıcı iptal edildi.")
        return redirect('core:hatirlatici_listesi')
    
    return render(request, 'core/hatirlaticilar/hatirlatici_sil.html', {'hatirlatici': hatirlatici})

@login_required
def hatirlatici_tamamla(request, hatirlatici_id):
    """Hatırlatıcı tamamlama"""
    hatirlatici = get_object_or_404(Hatirlatici, id=hatirlatici_id)
    
    # Yetki kontrolü
    if hatirlatici.kullanici != request.user:
        raise PermissionDenied("Bu hatırlatıcıyı tamamlama yetkiniz yok.")
    
    # Hatırlatıcıyı tamamla
    hatirlatici.durum = Hatirlatici.DURUM_TAMAMLANDI
    hatirlatici.save()
    
    messages.success(request, "Hatırlatıcı tamamlandı.")
    
    # AJAX isteği mi kontrol et
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('core:hatirlatici_listesi')

@login_required
def yapilacak_listesi(request):
    """Kullanıcının yapılacaklar listesi"""
    # Aktif yapılacaklar
    aktif_yapilacaklar = YapilacakListesi.objects.filter(
        kullanici=request.user, 
        durum=YapilacakListesi.DURUM_AKTIF
    ).order_by('oncelik', 'son_tarih', 'olusturulma_tarihi')
    
    # Tamamlanan ve iptal edilen yapılacaklar
    tamamlanan_yapilacaklar = YapilacakListesi.objects.filter(
        kullanici=request.user, 
        durum=YapilacakListesi.DURUM_TAMAMLANDI
    ).order_by('-guncelleme_tarihi')
    
    iptal_edilen_yapilacaklar = YapilacakListesi.objects.filter(
        kullanici=request.user, 
        durum=YapilacakListesi.DURUM_IPTAL
    ).order_by('-guncelleme_tarihi')
    
    context = {
        'aktif_yapilacaklar': aktif_yapilacaklar,
        'tamamlanan_yapilacaklar': tamamlanan_yapilacaklar,
        'iptal_edilen_yapilacaklar': iptal_edilen_yapilacaklar,
    }
    return render(request, 'core/yapilacaklar/yapilacak_listesi.html', context)

@login_required
def yapilacak_ekle(request):
    """Yeni yapılacak ekleme"""
    if request.method == 'POST':
        form = YapilacakListesiForm(request.POST)
        if form.is_valid():
            yapilacak = form.save(commit=False)
            yapilacak.kullanici = request.user
            yapilacak.save()
            messages.success(request, "Yapılacak görev başarıyla oluşturuldu.")
            return redirect('core:yapilacak_listesi')
    else:
        form = YapilacakListesiForm()
    
    return render(request, 'core/yapilacaklar/yapilacak_form.html', 
                 {'form': form, 'baslik': 'Yeni Yapılacak Ekle'})

@login_required
def yapilacak_detay(request, yapilacak_id):
    """Yapılacak detayları"""
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Yetki kontrolü
    if yapilacak.kullanici != request.user:
        raise PermissionDenied("Bu görevi görüntüleme yetkiniz yok.")
    
    return render(request, 'core/yapilacaklar/yapilacak_detay.html', {'yapilacak': yapilacak})

@login_required
def yapilacak_duzenle(request, yapilacak_id):
    """Yapılacak düzenleme"""
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Yetki kontrolü
    if yapilacak.kullanici != request.user:
        raise PermissionDenied("Bu görevi düzenleme yetkiniz yok.")
    
    if request.method == 'POST':
        form = YapilacakListesiForm(request.POST, instance=yapilacak)
        if form.is_valid():
            form.save()
            messages.success(request, "Görev başarıyla güncellendi.")
            return redirect('core:yapilacak_detay', yapilacak_id=yapilacak.id)
    else:
        form = YapilacakListesiForm(instance=yapilacak)
    
    return render(request, 'core/yapilacaklar/yapilacak_form.html', 
                 {'form': form, 'baslik': 'Görevi Düzenle', 'yapilacak': yapilacak})

@login_required
def yapilacak_sil(request, yapilacak_id):
    """Yapılacak silme"""
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Yetki kontrolü
    if yapilacak.kullanici != request.user:
        raise PermissionDenied("Bu görevi silme yetkiniz yok.")
    
    if request.method == 'POST':
        # Görevi iptal et (silme yerine durumunu güncelle)
        yapilacak.durum = YapilacakListesi.DURUM_IPTAL
        yapilacak.save()
        messages.success(request, "Görev iptal edildi.")
        return redirect('core:yapilacak_listesi')
    
    return render(request, 'core/yapilacaklar/yapilacak_sil.html', {'yapilacak': yapilacak})

@login_required
def yapilacak_tamamla(request, yapilacak_id):
    """Yapılacak tamamlama"""
    yapilacak = get_object_or_404(YapilacakListesi, id=yapilacak_id)
    
    # Yetki kontrolü
    if yapilacak.kullanici != request.user:
        raise PermissionDenied("Bu görevi tamamlama yetkiniz yok.")
    
    # Görevi tamamla
    yapilacak.durum = YapilacakListesi.DURUM_TAMAMLANDI
    yapilacak.save()
    
    messages.success(request, "Görev tamamlandı.")
    
    # AJAX isteği mi kontrol et
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'success'})
    
    return redirect('core:yapilacak_listesi')

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


