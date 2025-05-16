from django.db import models
from django.utils import timezone

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
