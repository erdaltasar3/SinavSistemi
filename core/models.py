from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
import os
from django.utils import timezone
import random
import string

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
    soru_sayisi = models.PositiveIntegerField(default=0, verbose_name="Toplam Soru Sayısı")
    
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

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True, null=True, verbose_name="Telefon Numarası")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, verbose_name="Profil Fotoğrafı")
    date_of_birth = models.DateField(blank=True, null=True, verbose_name="Doğum Tarihi")
    phone_number_verified = models.BooleanField(default=False, verbose_name="Telefon Numarası Doğrulandı")
    email_verified = models.BooleanField(default=False, verbose_name="E-posta Doğrulandı")

    def __str__(self):
        return self.user.username + ' Profile'

class EmailVerification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Kullanıcı")
    email = models.EmailField(verbose_name="E-posta Adresi")
    code = models.CharField(max_length=6, unique=True, verbose_name="Doğrulama Kodu")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Oluşturulma Zamanı")
    is_used = models.BooleanField(default=False, verbose_name="Kullanıldı mı?")

    def is_expired(self):
        # Kodun 15 dakika içinde geçerli olduğunu varsayalım
        expiration_time = self.created_at + timezone.timedelta(minutes=15)
        return timezone.now() > expiration_time

    def __str__(self):
        return f"{self.user.username} - {self.email} - {self.code}"

    class Meta:
        verbose_name = "E-posta Doğrulama Kodu"
        verbose_name_plural = "E-posta Doğrulama Kodları"

@receiver(pre_save, sender=UserProfile)
def delete_old_profile_picture(sender, instance, **kwargs):
    if instance.pk:  # Eğer bu bir güncelleme ise
        try:
            old_instance = UserProfile.objects.get(pk=instance.pk)
            if old_instance.profile_picture and old_instance.profile_picture != instance.profile_picture:
                # Eski profil resmini sil
                if os.path.isfile(old_instance.profile_picture.path):
                    os.remove(old_instance.profile_picture.path)
        except UserProfile.DoesNotExist:
            pass

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


