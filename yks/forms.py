from django import forms
from .models import (
    Hedef, 
    HedefTuru, 
    CalismaPlanı, 
    CalismaOturumu, 
    Gorev, 
    Hatirlatici
)
from core.models import Ders, Konu
from django.utils import timezone

class HedefForm(forms.ModelForm):
    """Hedef ekleme formu"""
    class Meta:
        model = Hedef
        fields = [
            'baslik', 'aciklama', 'tur', 'baslangic_tarihi', 
            'bitis_tarihi', 'oncelik', 'ders'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hedef başlığını girin'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Hedef açıklamasını girin', 'rows': 3}),
            'tur': forms.Select(attrs={'class': 'form-select'}),
            'baslangic_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bitis_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
            'ders': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tur'].empty_label = "Hedef türünü seçin"
        self.fields['ders'].empty_label = "İlgili dersi seçin (isteğe bağlı)"
        self.fields['ders'].required = False
        
    def clean_bitis_tarihi(self):
        baslangic_tarihi = self.cleaned_data.get('baslangic_tarihi')
        bitis_tarihi = self.cleaned_data.get('bitis_tarihi')
        
        if bitis_tarihi and baslangic_tarihi and bitis_tarihi < baslangic_tarihi:
            raise forms.ValidationError("Bitiş tarihi, başlangıç tarihinden önce olamaz.")
        
        return bitis_tarihi

class HedefDuzenleForm(forms.ModelForm):
    """Hedef düzenleme formu"""
    class Meta:
        model = Hedef
        fields = [
            'baslik', 'aciklama', 'tur', 'baslangic_tarihi', 'bitis_tarihi',
            'hedef_durum', 'oncelik', 'tamamlanma_orani', 'ders'
        ]
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tur': forms.Select(attrs={'class': 'form-select'}),
            'baslangic_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'bitis_tarihi': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hedef_durum': forms.Select(attrs={'class': 'form-select'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
            'tamamlanma_orani': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'ders': forms.Select(attrs={'class': 'form-select'}),
        }

class CalismaPlanForm(forms.ModelForm):
    """Çalışma planı ekleme formu"""
    class Meta:
        model = CalismaPlanı
        fields = ['tarih', 'notlar']
        widgets = {
            'tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notlar': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Plan hakkında notlarınızı yazabilirsiniz'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # Yeni oluşturuluyorsa
            self.fields['tarih'].initial = timezone.localdate()

class CalismaOturumuForm(forms.ModelForm):
    """Çalışma oturumu ekleme formu"""
    class Meta:
        model = CalismaOturumu
        fields = ['ders', 'konu', 'baslangic_saati', 'bitis_saati', 'notlar']
        widgets = {
            'ders': forms.Select(attrs={'class': 'form-select'}),
            'konu': forms.Select(attrs={'class': 'form-select'}),
            'baslangic_saati': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'bitis_saati': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'notlar': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Oturum notları'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['konu'].queryset = Konu.objects.none()
        self.fields['konu'].required = False
        
        if 'ders' in self.data:
            try:
                ders_id = int(self.data.get('ders'))
                self.fields['konu'].queryset = Konu.objects.filter(unite__ders_id=ders_id).order_by('unite__sira_no', 'sira_no')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.ders:
            self.fields['konu'].queryset = Konu.objects.filter(unite__ders=self.instance.ders).order_by('unite__sira_no', 'sira_no')
    
    def clean(self):
        cleaned_data = super().clean()
        baslangic_saati = cleaned_data.get('baslangic_saati')
        bitis_saati = cleaned_data.get('bitis_saati')
        
        if baslangic_saati and bitis_saati:
            if bitis_saati <= baslangic_saati:
                raise forms.ValidationError("Bitiş saati, başlangıç saatinden sonra olmalıdır.")
            
            # Süre hesaplama (dakika olarak)
            baslangic_dk = baslangic_saati.hour * 60 + baslangic_saati.minute
            bitis_dk = bitis_saati.hour * 60 + bitis_saati.minute
            sure = bitis_dk - baslangic_dk
            
            if sure <= 0:
                raise forms.ValidationError("Geçerli bir çalışma süresi belirtmelisiniz.")
            
            cleaned_data['sure'] = sure
            
        return cleaned_data

class GorevForm(forms.ModelForm):
    """Görev ekleme formu"""
    class Meta:
        model = Gorev
        fields = ['baslik', 'aciklama', 'son_tarih', 'oncelik']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Görev başlığını girin'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Görev açıklamasını girin'}),
            'son_tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
        }

class GorevDuzenleForm(forms.ModelForm):
    """Görev düzenleme formu"""
    class Meta:
        model = Gorev
        fields = ['baslik', 'aciklama', 'son_tarih', 'durum', 'oncelik']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'son_tarih': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'durum': forms.Select(attrs={'class': 'form-select'}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
        }

class HatirlaticiForm(forms.ModelForm):
    """Hatırlatıcı ekleme formu"""
    class Meta:
        model = Hatirlatici
        fields = ['baslik', 'aciklama', 'hatirlatma_tarihi', 'tekrar', 'tekrar_periyodu', 'aktif']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hatırlatıcı başlığını girin'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Hatırlatıcı açıklamasını girin'}),
            'hatirlatma_tarihi': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'tekrar': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'tekrar_periyodu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Günlük, Haftalık, Aylık vb.'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tekrar_periyodu'].required = False
    
    def clean(self):
        cleaned_data = super().clean()
        tekrar = cleaned_data.get('tekrar')
        tekrar_periyodu = cleaned_data.get('tekrar_periyodu')
        
        if tekrar and not tekrar_periyodu:
            raise forms.ValidationError("Tekrar seçildiğinde tekrar periyodu belirtilmelidir.")
            
        return cleaned_data 