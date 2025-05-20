from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class SinavTurleri(models.Model):
    """Sınav sisteminde bulunan sınav türleri"""
    ad = models.CharField(max_length=50, verbose_name="Sınav Adı")
    kod = models.CharField(max_length=10, unique=True, verbose_name="Sınav Kodu")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    ikon = models.CharField(max_length=50, blank=True, null=True, verbose_name="İkon Kodu")
    url = models.CharField(max_length=100, verbose_name="URL")
    
    def __str__(self):
        return self.ad
    
    class Meta:
        verbose_name = "Sınav Türü"
        verbose_name_plural = "Sınav Türleri"

class SinavAltTur(models.Model):
    """Sınav türlerinin alt türleri (YKS -> TYT, AYT, YDT gibi)"""
    sinav_turu = models.ForeignKey(SinavTurleri, on_delete=models.CASCADE, related_name="alt_turler", verbose_name="Bağlı Olduğu Sınav")
    ad = models.CharField(max_length=100, verbose_name="Alt Tür Adı")
    kod = models.CharField(max_length=20, verbose_name="Alt Tür Kodu")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    ikon = models.CharField(max_length=50, blank=True, null=True, verbose_name="İkon Kodu")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return f"{self.sinav_turu.kod} - {self.ad}"
    
    class Meta:
        verbose_name = "Sınav Alt Türü"
        verbose_name_plural = "Sınav Alt Türleri"
        unique_together = ('sinav_turu', 'kod')

class Ders(models.Model):
    """Sınav türlerinde veya alt türlerinde bulunan dersler"""
    sinav_turu = models.ForeignKey(SinavTurleri, on_delete=models.CASCADE, related_name="dersler", verbose_name="Bağlı Olduğu Sınav Türü", blank=True, null=True)
    alt_tur = models.ForeignKey(SinavAltTur, on_delete=models.CASCADE, related_name="dersler", verbose_name="Bağlı Olduğu Alt Tür", blank=True, null=True)
    ad = models.CharField(max_length=100, verbose_name="Ders Adı")
    kod = models.CharField(max_length=20, verbose_name="Ders Kodu")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    ikon = models.CharField(max_length=50, blank=True, null=True, verbose_name="İkon Kodu") 
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        if self.alt_tur:
            return f"{self.alt_tur.kod} - {self.ad}"
        elif self.sinav_turu:
            return f"{self.sinav_turu.kod} - {self.ad}"
        else:
            return self.ad
    
    class Meta:
        verbose_name = "Ders"
        verbose_name_plural = "Dersler"
        unique_together = [('alt_tur', 'kod')]
        
    def clean(self):
        # Bir ders ya bir sınav türüne ya da bir alt türe bağlı olmalıdır, ikisi birden veya hiçbiri olamaz
        from django.core.exceptions import ValidationError
        
        if self.sinav_turu and self.alt_tur:
            raise ValidationError("Bir ders aynı anda hem sınav türüne hem de alt türe bağlı olamaz.")
        elif not self.sinav_turu and not self.alt_tur:
            raise ValidationError("Bir ders ya bir sınav türüne ya da bir alt türe bağlı olmalıdır.")
            
        # Eğer alt türe bağlıysa, sinav_turu'nu otomatik olarak alt türün bağlı olduğu sınav türü yap
        if self.alt_tur and not self.sinav_turu:
            self.sinav_turu = self.alt_tur.sinav_turu

class Unite(models.Model):
    """Derslere ait üniteler"""
    ders = models.ForeignKey(Ders, on_delete=models.CASCADE, related_name="uniteler", verbose_name="Bağlı Olduğu Ders")
    ad = models.CharField(max_length=200, verbose_name="Ünite Adı")
    sira_no = models.PositiveIntegerField(default=1, verbose_name="Sıra Numarası")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return f"{self.ders.ad} - {self.ad}"
    
    class Meta:
        verbose_name = "Ünite"
        verbose_name_plural = "Üniteler"
        ordering = ["ders", "sira_no"]
        unique_together = [("ders", "ad"), ("ders", "sira_no")]

class Konu(models.Model):
    """Ünitelere ait konular"""
    unite = models.ForeignKey(Unite, on_delete=models.CASCADE, related_name="konular", verbose_name="Bağlı Olduğu Ünite")
    ad = models.CharField(max_length=200, verbose_name="Konu Adı")
    sira_no = models.PositiveIntegerField(default=1, verbose_name="Sıra Numarası")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    aktif = models.BooleanField(default=True, verbose_name="Aktif")
    
    def __str__(self):
        return f"{self.unite.ad} - {self.ad}"
    
    class Meta:
        verbose_name = "Konu"
        verbose_name_plural = "Konular"
        ordering = ["unite", "sira_no"]
        unique_together = [("unite", "ad"), ("unite", "sira_no")]

# Hedef Belirleme ve Takip Modelleri

class CalismaHedefi(models.Model):
    """Kullanıcının çalışma hedefleri"""
    PERIYOT_GUNLUK = 'G'
    PERIYOT_HAFTALIK = 'H'
    PERIYOT_AYLIK = 'A'
    
    PERIYOT_CHOICES = [
        (PERIYOT_GUNLUK, 'Günlük'),
        (PERIYOT_HAFTALIK, 'Haftalık'),
        (PERIYOT_AYLIK, 'Aylık'),
    ]
    
    DURUM_AKTIF = 'A'
    DURUM_TAMAMLANDI = 'T'
    DURUM_IPTAL = 'I'
    
    DURUM_CHOICES = [
        (DURUM_AKTIF, 'Aktif'),
        (DURUM_TAMAMLANDI, 'Tamamlandı'),
        (DURUM_IPTAL, 'İptal Edildi'),
    ]
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name="calisma_hedefleri", verbose_name="Kullanıcı")
    baslik = models.CharField(max_length=200, verbose_name="Hedef Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    baslangic_tarihi = models.DateField(verbose_name="Başlangıç Tarihi")
    bitis_tarihi = models.DateField(verbose_name="Bitiş Tarihi")
    periyot = models.CharField(max_length=1, choices=PERIYOT_CHOICES, default=PERIYOT_GUNLUK, verbose_name="Periyot")
    durum = models.CharField(max_length=1, choices=DURUM_CHOICES, default=DURUM_AKTIF, verbose_name="Durum")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"
    
    class Meta:
        verbose_name = "Çalışma Hedefi"
        verbose_name_plural = "Çalışma Hedefleri"
        ordering = ["-olusturulma_tarihi"]

class CalismaPlani(models.Model):
    """Kullanıcının günlük/haftalık çalışma planları"""
    PLAN_TURU_DERS = 'D'
    PLAN_TURU_KONU = 'K'
    PLAN_TURU_DENEME = 'M'
    
    PLAN_TURU_CHOICES = [
        (PLAN_TURU_DERS, 'Ders Çalışma'),
        (PLAN_TURU_KONU, 'Konu Tekrarı'),
        (PLAN_TURU_DENEME, 'Deneme Sınavı'),
    ]
    
    DURUM_BEKLIYOR = 'B'
    DURUM_TAMAMLANDI = 'T'
    DURUM_IPTAL = 'I'
    
    DURUM_CHOICES = [
        (DURUM_BEKLIYOR, 'Bekliyor'),
        (DURUM_TAMAMLANDI, 'Tamamlandı'),
        (DURUM_IPTAL, 'İptal Edildi'),
    ]
    
    hedef = models.ForeignKey(CalismaHedefi, on_delete=models.CASCADE, related_name="calisma_planlari", verbose_name="Bağlı Olduğu Hedef")
    baslik = models.CharField(max_length=200, verbose_name="Plan Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    plan_turu = models.CharField(max_length=1, choices=PLAN_TURU_CHOICES, verbose_name="Plan Türü")
    ders = models.ForeignKey(Ders, on_delete=models.SET_NULL, null=True, blank=True, related_name="calisma_planlari", verbose_name="Ders")
    konu = models.ForeignKey(Konu, on_delete=models.SET_NULL, null=True, blank=True, related_name="calisma_planlari", verbose_name="Konu")
    planlanan_tarih = models.DateField(verbose_name="Planlanan Tarih")
    planlanan_sure = models.PositiveIntegerField(verbose_name="Planlanan Süre (dakika)")
    gerceklesen_sure = models.PositiveIntegerField(default=0, verbose_name="Gerçekleşen Süre (dakika)")
    durum = models.CharField(max_length=1, choices=DURUM_CHOICES, default=DURUM_BEKLIYOR, verbose_name="Durum")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.hedef.kullanici.username} - {self.baslik} ({self.planlanan_tarih})"
    
    class Meta:
        verbose_name = "Çalışma Planı"
        verbose_name_plural = "Çalışma Planları"
        ordering = ["planlanan_tarih", "olusturulma_tarihi"]

class Hatirlatici(models.Model):
    """Kullanıcı hatırlatıcıları"""
    ONCELIK_DUSUK = 'D'
    ONCELIK_NORMAL = 'N'
    ONCELIK_YUKSEK = 'Y'
    
    ONCELIK_CHOICES = [
        (ONCELIK_DUSUK, 'Düşük'),
        (ONCELIK_NORMAL, 'Normal'),
        (ONCELIK_YUKSEK, 'Yüksek'),
    ]
    
    DURUM_AKTIF = 'A'
    DURUM_TAMAMLANDI = 'T'
    DURUM_IPTAL = 'I'
    
    DURUM_CHOICES = [
        (DURUM_AKTIF, 'Aktif'),
        (DURUM_TAMAMLANDI, 'Tamamlandı'),
        (DURUM_IPTAL, 'İptal Edildi'),
    ]
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name="hatirlaticilar", verbose_name="Kullanıcı")
    baslik = models.CharField(max_length=200, verbose_name="Hatırlatıcı Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    tarih = models.DateField(verbose_name="Tarih")
    saat = models.TimeField(blank=True, null=True, verbose_name="Saat")
    oncelik = models.CharField(max_length=1, choices=ONCELIK_CHOICES, default=ONCELIK_NORMAL, verbose_name="Öncelik")
    durum = models.CharField(max_length=1, choices=DURUM_CHOICES, default=DURUM_AKTIF, verbose_name="Durum")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik} ({self.tarih})"
    
    class Meta:
        verbose_name = "Hatırlatıcı"
        verbose_name_plural = "Hatırlatıcılar"
        ordering = ["tarih", "saat"]

class YapilacakListesi(models.Model):
    """Kullanıcının yapılacaklar listesi"""
    ONCELIK_DUSUK = 'D'
    ONCELIK_NORMAL = 'N'
    ONCELIK_YUKSEK = 'Y'
    
    ONCELIK_CHOICES = [
        (ONCELIK_DUSUK, 'Düşük'),
        (ONCELIK_NORMAL, 'Normal'),
        (ONCELIK_YUKSEK, 'Yüksek'),
    ]
    
    DURUM_AKTIF = 'A'
    DURUM_TAMAMLANDI = 'T'
    DURUM_IPTAL = 'I'
    
    DURUM_CHOICES = [
        (DURUM_AKTIF, 'Aktif'),
        (DURUM_TAMAMLANDI, 'Tamamlandı'),
        (DURUM_IPTAL, 'İptal Edildi'),
    ]
    
    kullanici = models.ForeignKey(User, on_delete=models.CASCADE, related_name="yapilacaklar", verbose_name="Kullanıcı")
    baslik = models.CharField(max_length=200, verbose_name="Görev Başlığı")
    aciklama = models.TextField(blank=True, null=True, verbose_name="Açıklama")
    son_tarih = models.DateField(blank=True, null=True, verbose_name="Son Tarih")
    oncelik = models.CharField(max_length=1, choices=ONCELIK_CHOICES, default=ONCELIK_NORMAL, verbose_name="Öncelik")
    durum = models.CharField(max_length=1, choices=DURUM_CHOICES, default=DURUM_AKTIF, verbose_name="Durum")
    olusturulma_tarihi = models.DateTimeField(auto_now_add=True)
    guncelleme_tarihi = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.kullanici.username} - {self.baslik}"
    
    class Meta:
        verbose_name = "Yapılacak"
        verbose_name_plural = "Yapılacaklar"
        ordering = ["durum", "oncelik", "son_tarih", "olusturulma_tarihi"]



