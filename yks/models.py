from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from core.models import Ders, Konu
from django.urls import reverse

# Create your models here.

class YKSOturum(models.Model):
    """YKS sınavı oturumları (TYT, AYT, YDT)"""
    
    DURUM_BEKLIYOR = 'Bekliyor'
    DURUM_GECMIS = 'Geçmiş'
    
    DURUM_CHOICES = [
        (DURUM_BEKLIYOR, 'Bekliyor'),
        (DURUM_GECMIS, 'Geçmiş'),
    ]
    
    ad = models.CharField(max_length=50)
    kod = models.CharField(max_length=10)
    yil = models.IntegerField(verbose_name="Sınav Yılı", default=timezone.now().year)
    aciklama = models.TextField(blank=True, null=True)
    sinav_tarihi = models.DateTimeField(blank=True, null=True, verbose_name="Sınav Tarihi")
    durum = models.CharField(
        max_length=15,
        choices=DURUM_CHOICES,
        default=DURUM_BEKLIYOR,
        verbose_name="Durum"
    )
    
    def __str__(self):
        return f"{self.ad} ({self.yil})"
    
    def save(self, *args, **kwargs):
        # Sınav tarihi geçmişse otomatik olarak durum "Geçmiş" olarak işaretle
        if self.sinav_tarihi:
            # Timezone bilgisini kontrol et
            if timezone.is_naive(self.sinav_tarihi):
                sinav_tarihi = timezone.make_aware(self.sinav_tarihi)
            else:
                sinav_tarihi = self.sinav_tarihi
                
            if sinav_tarihi < timezone.now():
                self.durum = self.DURUM_GECMIS
        
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = "YKS Oturum"
        verbose_name_plural = "YKS Oturumları"
        unique_together = ('kod', 'yil')  # Aynı yılda aynı kod tekrar edemez


class KonuTakip(models.Model):
    """Kullanıcının tamamladığı konuları takip etmek için kullanılır"""
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='tamamlanan_konular', verbose_name="Kullanıcı")
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE, related_name='tamamlayanlar', verbose_name="Konu")
    tamamlandi = models.BooleanField(default=True, verbose_name="Tamamlandı")
    tamamlanma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Tamamlanma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.konu}"
    
    class Meta:
        verbose_name = "Konu Takip"
        verbose_name_plural = "Konu Takipleri"
        ordering = ['-tamamlanma_tarihi']
        unique_together = ('kullanici', 'konu')  # Bir kullanıcı bir konuyu yalnızca bir kez tamamlayabilir


# Hedef Belirleme ve Takip Modelleri
class HedefTuru(models.Model):
    """Hedef türleri (günlük, haftalık, aylık, özel)"""
    
    GUNLUK = 'Günlük'
    HAFTALIK = 'Haftalık'
    AYLIK = 'Aylık'
    OZEL = 'Özel'
    
    TUR_CHOICES = [
        (GUNLUK, 'Günlük'),
        (HAFTALIK, 'Haftalık'),
        (AYLIK, 'Aylık'),
        (OZEL, 'Özel')
    ]
    
    ad = models.CharField(max_length=20, choices=TUR_CHOICES, default=GUNLUK, verbose_name="Hedef Türü")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    
    def __str__(self):
        return self.ad
    
    class Meta:
        verbose_name = "Hedef Türü"
        verbose_name_plural = "Hedef Türleri"


class HedefDurum(models.Model):
    """Hedeflerin durumları (Aktif, Tamamlandı, Tamamlanmadı, vb.)"""
    ad = models.CharField(max_length=50, unique=True, verbose_name="Durum Adı")

    def __str__(self):
        return self.ad

    class Meta:
        verbose_name = "Hedef Durumu"
        verbose_name_plural = "Hedef Durumları"


class Hedef(models.Model):
    """Kullanıcının belirlediği çalışma hedefleri"""
    
    ONCELIK_DUSUK = 'Düşük'
    ONCELIK_ORTA = 'Orta'
    ONCELIK_YUKSEK = 'Yüksek'
    
    ONCELIK_CHOICES = [
        (ONCELIK_DUSUK, 'Düşük'),
        (ONCELIK_ORTA, 'Orta'),
        (ONCELIK_YUKSEK, 'Yüksek')
    ]
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hedefler', verbose_name="Kullanıcı")
    baslik = models.CharField(max_length=200, verbose_name="Hedef Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    tur = models.ForeignKey(HedefTuru, on_delete=models.CASCADE, related_name='hedefler', verbose_name="Hedef Türü")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi", default=timezone.now)
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi", blank=True, null=True)
    hedef_durum = models.ForeignKey(HedefDurum, on_delete=models.SET_NULL, null=True, related_name='hedefler', verbose_name="Hedef Durumu")
    oncelik = models.CharField(max_length=10, choices=ONCELIK_CHOICES, default=ONCELIK_ORTA, verbose_name="Öncelik")
    tamamlanma_orani = models.IntegerField(default=0, verbose_name="Tamamlanma Oranı (%)")
    ders = models.ForeignKey(Ders, on_delete=models.SET_NULL, blank=True, null=True, related_name='hedefler', verbose_name="İlgili Ders")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"
    
    class Meta:
        verbose_name = "Hedef"
        verbose_name_plural = "Hedefler"
        ordering = ['-olusturma_tarihi']


class CalismaPlanı(models.Model):
    """Günlük çalışma planları"""
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='calisma_planlari', verbose_name="Kullanıcı")
    tarih = models.DateField(verbose_name="Çalışma Tarihi", default=timezone.now)
    toplam_calisma_suresi = models.PositiveIntegerField(default=0, verbose_name="Toplam Çalışma Süresi (dakika)")
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.tarih}"
    
    def get_absolute_url(self):
        return reverse('yks:calisma_plani_detay', kwargs={'plan_id': self.pk})
    
    class Meta:
        verbose_name = "Çalışma Planı"
        verbose_name_plural = "Çalışma Planları"
        ordering = ['-tarih']
        unique_together = ('kullanici', 'tarih')  # Bir kullanıcı bir gün için tek bir plan oluşturabilir


class CalismaOturumu(models.Model):
    """Çalışma planına bağlı oturumlar"""
    
    plan = models.ForeignKey(CalismaPlanı, on_delete=models.CASCADE, related_name='oturumlar', verbose_name="Çalışma Planı")
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, related_name='calisma_oturumlari', verbose_name="Ders")
    konu = models.ForeignKey(Konu, on_delete=models.SET_NULL, blank=True, null=True, related_name='calisma_oturumlari', verbose_name="Konu")
    baslangic_saati = models.TimeField(verbose_name="Başlangıç Saati")
    bitis_saati = models.TimeField(verbose_name="Bitiş Saati")
    sure = models.PositiveIntegerField(verbose_name="Süre (dakika)")
    tamamlandi = models.BooleanField(default=False, verbose_name="Tamamlandı")
    notlar = models.TextField(blank=True, null=True, verbose_name="Notlar")
    
    def __str__(self):
        return f"{self.ders.ad} - {self.baslangic_saati} - {self.bitis_saati}"
    
    class Meta:
        verbose_name = "Çalışma Oturumu"
        verbose_name_plural = "Çalışma Oturumları"
        ordering = ['baslangic_saati']


class Hatirlatici(models.Model):
    """Çalışma hatırlatıcıları"""
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name='hatirlaticilar', verbose_name="Kullanıcı")
    baslik = models.CharField(max_length=200, verbose_name="Hatırlatıcı Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    hatirlatma_tarihi = models.DateTimeField(verbose_name="Hatırlatma Tarihi ve Saati")
    tekrar = models.BooleanField(default=False, verbose_name="Tekrarla")
    tekrar_periyodu = models.CharField(max_length=20, blank=True, null=True, verbose_name="Tekrar Periyodu")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    olusturma_tarihi = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturma Tarihi")
    guncelleme_tarihi = models.DateTimeField(auto_now=True, verbose_name="Güncelleme Tarihi")
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"
    
    class Meta:
        verbose_name = "Hatırlatıcı"
        verbose_name_plural = "Hatırlatıcılar"
        ordering = ['hatirlatma_tarihi']


# --- Hedef Detay Modelleri (Soru Çözümü ve Konu Takip) ---

class SoruCozumHedefi(models.Model):
    hedef = models.OneToOneField('Hedef', on_delete=models.CASCADE, related_name='soru_cozum_detay')
    toplam_soru = models.PositiveIntegerField(verbose_name="Toplam Soru Hedefi")
    cozulmus_soru = models.PositiveIntegerField(default=0, verbose_name="Çözülen Soru")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    # Ders ilişkisi hedef üzerinden alınır

    def __str__(self):
        return f"{self.hedef} - {self.toplam_soru} Soru"

    def ilerleme_orani(self):
        if self.toplam_soru > 0:
            return int((self.cozulmus_soru / self.toplam_soru) * 100)
        return 0

    class Meta:
        verbose_name = "Soru Çözüm Hedefi"
        verbose_name_plural = "Soru Çözüm Hedefleri"

class KonuTakipHedefi(models.Model):
    hedef = models.OneToOneField('Hedef', on_delete=models.CASCADE, related_name='konu_takip_detay')
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, verbose_name="Ders")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")

    def __str__(self):
        return f"{self.hedef} - {self.ders}"

    def ilerleme_orani(self):
        toplam = self.konular.count()
        tamamlanan = self.konular.filter(tamamlandi=True).count()
        if toplam > 0:
            return int((tamamlanan / toplam) * 100)
        return 0

    class Meta:
        verbose_name = "Konu Takip Hedefi"
        verbose_name_plural = "Konu Takip Hedefleri"

class KonuTakipHedefKonu(models.Model):
    konu_takip_hedefi = models.ForeignKey(KonuTakipHedefi, on_delete=models.CASCADE, related_name='konular')
    konu = models.ForeignKey(Konu, on_delete=models.CASCADE, verbose_name="Konu")
    tamamlandi = models.BooleanField(default=False, verbose_name="Tamamlandı mı?")

    def __str__(self):
        return f"{self.konu_takip_hedefi} - {self.konu}"

    class Meta:
        verbose_name = "Konu Takip Hedef Konusu"
        verbose_name_plural = "Konu Takip Hedef Konuları"
        unique_together = ('konu_takip_hedefi', 'konu')




