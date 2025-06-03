from django import forms
from .models import (
    Hedef, 
    HedefTuru, 
    CalismaPlanı, 
    CalismaOturumu, 
    Hatirlatici
)
from core.models import Ders, Konu, UserProfile
from django.utils import timezone
from django.contrib.auth.models import User

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
    
    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if not self.instance.pk:  # Yeni oluşturuluyorsa
            self.fields['tarih'].initial = timezone.localdate()

    def clean_tarih(self):
        tarih = self.cleaned_data.get('tarih')
        if not tarih:
            return tarih

        # Seçilen tarih için kullanıcının zaten bir planı var mı kontrol et
        if self.instance.pk: # Eğer plan düzenleniyorsa, mevcut planı hariç tut
            existing_plan = CalismaPlanı.objects.filter(kullanici=self.user, tarih=tarih).exclude(pk=self.instance.pk).exists()
        else:
            # Yeni plan oluşturuluyorsa, sadece tarih ve kullanıcıya göre kontrol et
            if not hasattr(self, 'user'):
                 raise forms.ValidationError("Kullanıcı bilgisi forma aktarılmamış.") # Sanity check
            existing_plan = CalismaPlanı.objects.filter(kullanici=self.user, tarih=tarih).exists()

        if existing_plan:
            raise forms.ValidationError("Bu tarih için zaten bir çalışma planınız var.")

        return tarih

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

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False, label='Ad')
    last_name = forms.CharField(max_length=150, required=False, label='Soyad')
    email = forms.EmailField(max_length=254, required=False, label='E-posta', disabled=True)

    class Meta:
        model = UserProfile
        fields = ['phone_number', 'profile_picture']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(UserProfileForm, self).__init__(*args, **kwargs)
        
        if user:
            self.fields['first_name'].initial = user.first_name
            self.fields['last_name'].initial = user.last_name
            self.fields['email'].initial = user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        user = profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        # E-posta değiştirilemez olduğu için burada güncelleme yapmıyoruz
        
        if commit:
            user.save()
            profile.save()
        return profile 