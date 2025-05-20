from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import CalismaHedefi, CalismaPlani, Hatirlatici, YapilacakListesi, Ders, Konu

class KayitFormu(UserCreationForm):
    """Kullanıcı kayıt formu"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi'})
    )
    first_name = forms.CharField(
        required=True, max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınız'})
    )
    last_name = forms.CharField(
        required=True, max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınız'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Şifre'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Şifre (Tekrar)'})
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email

class GirisFormu(AuthenticationForm):
    """Kullanıcı giriş formu"""
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'})
    )

# Hedef Belirleme ve Takip için formlar

class CalismaHedefiForm(forms.ModelForm):
    """Çalışma hedefi oluşturma/düzenleme formu"""
    baslangic_tarihi = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Başlangıç Tarihi"
    )
    bitis_tarihi = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Bitiş Tarihi"
    )
    
    class Meta:
        model = CalismaHedefi
        fields = ['baslik', 'aciklama', 'baslangic_tarihi', 'bitis_tarihi', 'periyot']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hedef başlığı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Hedef açıklaması', 'rows': 4}),
            'periyot': forms.Select(attrs={'class': 'form-select'}),
        }
        
    def clean(self):
        cleaned_data = super().clean()
        baslangic_tarihi = cleaned_data.get('baslangic_tarihi')
        bitis_tarihi = cleaned_data.get('bitis_tarihi')
        
        if baslangic_tarihi and bitis_tarihi and baslangic_tarihi > bitis_tarihi:
            raise ValidationError("Başlangıç tarihi bitiş tarihinden sonra olamaz.")
        
        return cleaned_data

class CalismaPlaniForm(forms.ModelForm):
    """Çalışma planı oluşturma/düzenleme formu"""
    planlanan_tarih = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Planlanan Tarih"
    )
    
    class Meta:
        model = CalismaPlani
        fields = ['baslik', 'aciklama', 'plan_turu', 'ders', 'konu', 'planlanan_tarih', 'planlanan_sure']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Plan başlığı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Plan açıklaması', 'rows': 3}),
            'plan_turu': forms.Select(attrs={'class': 'form-select'}),
            'ders': forms.Select(attrs={'class': 'form-select'}),
            'konu': forms.Select(attrs={'class': 'form-select'}),
            'planlanan_sure': forms.NumberInput(attrs={'class': 'form-control', 'min': 10, 'placeholder': 'Dakika olarak süre'})
        }
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        hedef_id = kwargs.pop('hedef_id', None)
        super().__init__(*args, **kwargs)
        
        # Hedef alanını otomatik doldur
        if hedef_id:
            self.fields['hedef'] = forms.ModelChoiceField(
                queryset=CalismaHedefi.objects.filter(id=hedef_id),
                widget=forms.HiddenInput(),
                initial=hedef_id
            )
        else:
            self.fields['hedef'] = forms.ModelChoiceField(
                queryset=CalismaHedefi.objects.filter(kullanici=user, durum=CalismaHedefi.DURUM_AKTIF),
                widget=forms.Select(attrs={'class': 'form-select'}),
                label="Hedef"
            )
            
        # Plan türüne göre ilgili alanları göster/gizle için JavaScript uygulanacak
        
    def clean(self):
        cleaned_data = super().clean()
        plan_turu = cleaned_data.get('plan_turu')
        ders = cleaned_data.get('ders')
        konu = cleaned_data.get('konu')
        
        if plan_turu == CalismaPlani.PLAN_TURU_DERS and not ders:
            raise ValidationError({"ders": "Ders çalışma planı için ders seçimi zorunludur."})
            
        if plan_turu == CalismaPlani.PLAN_TURU_KONU and not konu:
            raise ValidationError({"konu": "Konu tekrarı planı için konu seçimi zorunludur."})
            
        return cleaned_data

class HatirlaticiForm(forms.ModelForm):
    """Hatırlatıcı oluşturma/düzenleme formu"""
    tarih = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Tarih"
    )
    saat = forms.TimeField(
        widget=forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
        label="Saat",
        required=False
    )
    
    class Meta:
        model = Hatirlatici
        fields = ['baslik', 'aciklama', 'tarih', 'saat', 'oncelik']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hatırlatıcı başlığı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Hatırlatıcı açıklaması', 'rows': 3}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
        }

class YapilacakListesiForm(forms.ModelForm):
    """Yapılacaklar listesi öğesi oluşturma/düzenleme formu"""
    son_tarih = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Son Tarih",
        required=False
    )
    
    class Meta:
        model = YapilacakListesi
        fields = ['baslik', 'aciklama', 'son_tarih', 'oncelik']
        widgets = {
            'baslik': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Görev başlığı'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Görev açıklaması', 'rows': 3}),
            'oncelik': forms.Select(attrs={'class': 'form-select'}),
        }

class PlanTamamlamaForm(forms.ModelForm):
    """Çalışma planı tamamlama formu"""
    class Meta:
        model = CalismaPlani
        fields = ['gerceklesen_sure', 'durum']
        widgets = {
            'gerceklesen_sure': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'durum': forms.Select(attrs={'class': 'form-select'}),
        } 