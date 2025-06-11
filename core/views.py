from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse, Http404
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.db.models import Count, Avg, Q
from django.core.mail import send_mail
from django.conf import settings
import json
import random
import string
from .forms import (
    KayitFormu, GirisFormu, UserProfileForm,
    DersForm, UniteForm, KonuForm
)
from django.contrib.auth.models import User
from .models import (
    SinavTurleri, SinavAltTur, Ders, Unite, Konu, EmailVerification, UserProfile
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
                # Özel mesaj için session kullan, genel Django mesaj sistemini değil
                request.session['auth_message'] = {
                    'type': 'login_success',
                    'text': f"Merhaba {user.first_name if user.first_name else user.username}! Başarıyla giriş yaptınız.",
                    'timestamp': timezone.now().timestamp()
                }
                
                if user.is_staff or user.is_superuser:
                    return redirect('core:yetkili_panel')
                return redirect('index')
        else:
            # Form geçerli değilse, form'daki hata mesajlarını kullan
            if form.non_field_errors():
                messages.error(request, form.non_field_errors()[0])
            elif 'username' in form.errors:
                messages.error(request, form.errors['username'][0])
            elif 'password' in form.errors:
                messages.error(request, form.errors['password'][0])
            else:
                messages.error(request, "Giriş yapılırken bir hata oluştu. Lütfen tekrar deneyiniz.")
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
            # Özel mesaj ekle
            request.session['register_success'] = True
            request.session['register_username'] = user.first_name if user.first_name else user.username
            
            return redirect('index')
        else:
            # Hataları öncelikli olarak göster - sıralama önemli!
            error_fields = [
                'first_name',  # Önce ad
                'last_name',   # Sonra soyad
                'username',    # Sonra kullanıcı adı
                'email',       # Sonra email (isteğe bağlı)
                'password1',   # Sonra şifre
                'password2',   # En son şifre tekrarı
            ]
            
            # İlk hatayı bul ve göster
            for field in error_fields:
                if field in form.errors:
                    error_msg = form.errors[field][0]
                    messages.error(request, f"{error_msg}")
                    break  # İlk hatayı gösterdikten sonra dur
            
            # Hiçbir alanda hata bulunamazsa (nadiren olur ama kontrol edelim)
            if not messages.get_messages(request):
                messages.error(request, "Formda hatalar var, lütfen kontrol ediniz.")
    else:
        form = KayitFormu()
    
    return render(request, 'core/kayit.html', {'form': form})

def cikis_view(request):
    """Kullanıcı çıkışı"""
    # Çıkış yapan kullanıcının adını önceden kaydedelim
    username = ""
    if request.user.is_authenticated:
        username = request.user.first_name if request.user.first_name else request.user.username
    
    logout(request)
    
    # Özel mesaj için session kullan, genel Django mesaj sistemini değil
    request.session['auth_message'] = {
        'type': 'logout_success',
        'text': f"Görüşmek üzere {username}! Oturumunuz güvenli bir şekilde sonlandırıldı." if username else "Oturumunuz güvenli bir şekilde sonlandırıldı.",
        'timestamp': timezone.now().timestamp()
    }
    
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
    # Auth mesajlarını kontrol et - özel mesaj kutusuna konulacak, normal mesaj sistemini kullanmıyoruz
    auth_message = request.session.pop('auth_message', None)
    
    # Mesaj içeriğinden JSON oluştur
    auth_message_json = 'null'
    if auth_message:
        auth_message_json = json.dumps(auth_message)
    
    # Kullanıcı oturum açmışsa
    if request.user.is_authenticated:
        # Sınav türlerini getir
        sinav_turleri = SinavTurleri.objects.filter(aktif=True)
        
        context = {
            'sinav_turleri': sinav_turleri,
            'auth_message_json': auth_message_json
        }
        
        return render(request, 'core/index.html', context)
    
    # Oturum açmamışsa
    return render(request, 'core/index.html', {'auth_message_json': auth_message_json})

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
    user = request.user

    # Kullanıcının mevcut e-posta adresini al
    current_email = user.email

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            # Formdan gelen yeni e-posta adresini al
            new_email = form.cleaned_data.get('email')

            # Eğer e-posta adresi değiştiyse, email_verified'ı False yap ve User modelindeki email'i güncelle
            if new_email and new_email != current_email:
                user.email = new_email
                user.save()
                user_profile.email_verified = False

            # user_profile formunu kaydet
            form.save()

            # Başarılı mesajı ekle ve profil sayfasına yönlendir
            messages.success(request, 'Profil bilgileriniz başarıyla güncellendi.')
            return redirect('core:profile')
        else:
            # Form geçerli değilse hataları JSON olarak döndür (AJAX form validation için)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                 return JsonResponse({'success': False, 'errors': form.errors.get_json_data()})
            else:
                # Normal form submit ise hatalarla birlikte sayfayı yeniden render et
                messages.error(request, 'Lütfen formdaki hataları düzeltin.')

    else:
        # Formu User instance'ı ile başlat
        form = UserProfileForm(instance=user_profile, initial={'email': user.email})

    context = {
        'form': form
    }
    return render(request, 'core/profile.html', context)

@login_required
def send_verification_email(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = request.user

        if not email:
            return JsonResponse({'success': False, 'message': 'E-posta adresi boş olamaz.'})

        # Daha önce gönderilmiş ve kullanılmamış kodları geçersiz kıl
        EmailVerification.objects.filter(user=user, is_used=False).update(is_used=True)

        # Yeni doğrulama kodu oluştur
        code = ''.join(random.choices(string.digits, k=6))

        # Doğrulama kaydını oluştur
        EmailVerification.objects.create(user=user, email=email, code=code)

        # E-posta gönderme işlemi (Ayarların yapılmış olması gerekir)
        subject = 'E-posta Doğrulama Kodunuz'
        message = f'E-posta doğrulama kodunuz: {code}'
        email_from = settings.EMAIL_HOST_USER
        recipient_list = [email]

        try:
            send_mail(subject, message, email_from, recipient_list)
            return JsonResponse({'success': True, 'message': 'Doğrulama kodu e-posta adresinize gönderildi.'})
        except Exception as e:
            # Log the error for debugging
            print(f"Error sending email: {e}")
            return JsonResponse({'success': False, 'message': 'E-posta gönderilirken bir hata oluştu. Lütfen daha sonra tekrar deneyin.'})

    return JsonResponse({'success': False, 'message': 'Geçersiz istek yöntemi.'})

@login_required
def verify_email_code(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        code = request.POST.get('code')
        user = request.user

        if not email or not code:
            return JsonResponse({'success': False, 'message': 'E-posta adresi ve doğrulama kodu boş olamaz.'})

        try:
            # En son gönderilen ve kullanılmamış doğrulama kodunu al
            verification_entry = EmailVerification.objects.filter(user=user, email=email, is_used=False).latest('created_at')

            # Kodun süresinin dolup dolmadığını kontrol et
            if verification_entry.is_expired():
                return JsonResponse({'success': False, 'message': 'Doğrulama kodunun süresi dolmuş. Lütfen yeni bir kod gönderin.'})

            # Kodları karşılaştır
            if verification_entry.code == code:
                # Doğrulama başarılı, is_used olarak işaretle
                verification_entry.is_used = True
                verification_entry.save()

                # Kullanıcının e-posta adresini doğrulanmış olarak işaretle
                user.userprofile.email_verified = True
                user.userprofile.save()

                return JsonResponse({'success': True, 'message': 'E-posta adresiniz başarıyla doğrulandı.'})
            else:
                return JsonResponse({'success': False, 'message': 'Hatalı doğrulama kodu.'})

        except EmailVerification.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'E-posta adresinize ait bekleyen doğrulama kodu bulunamadı.'})
        except Exception as e:
             # Log the error for debugging
            print(f"Error verifying email code: {e}")
            return JsonResponse({'success': False, 'message': 'Doğrulama sırasında bir hata oluştu.'})

    return JsonResponse({'success': False, 'message': 'Geçersiz istek yöntemi.'})


