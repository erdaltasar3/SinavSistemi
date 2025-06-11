from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import Ders, Konu, Unite, UserProfile

class KayitFormu(UserCreationForm):
    """Kullanıcı kayıt formu"""
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi (İsteğe bağlı)'})
    )
    first_name = forms.CharField(
        required=True, max_length=30,
        error_messages={'required': 'Adınızı girmelisiniz.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınız'})
    )
    last_name = forms.CharField(
        required=True, max_length=30,
        error_messages={'required': 'Soyadınızı girmelisiniz.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınız'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2')
        error_messages = {
            'username': {
                'required': 'Kullanıcı adı girmelisiniz.',
                'unique': 'Bu kullanıcı adı zaten kullanılıyor.',
                'invalid': 'Geçerli bir kullanıcı adı giriniz (sadece harfler, rakamlar ve @/./+/-/_ karakterleri).'
            }
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Şifre'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Şifre (Tekrar)'})
        
        # Şifre alanları için özel hata mesajları
        self.fields['password1'].error_messages = {
            'required': 'Şifre girmelisiniz.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Şifre tekrarını girmelisiniz.',
        }
        
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:  # Sadece e-posta girilmişse kontrol et
            if User.objects.filter(email=email).exists():
                raise ValidationError('Bu e-posta adresi zaten kullanılıyor.')
        return email

class GirisFormu(AuthenticationForm):
    """Kullanıcı giriş formu"""
    username = forms.CharField(
        error_messages={'required': 'Kullanıcı adınızı girmelisiniz.'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Kullanıcı Adı'})
    )
    password = forms.CharField(
        error_messages={'required': 'Şifrenizi girmelisiniz.'},
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Şifre'})
    )
    
    error_messages = {
        'invalid_login': 'Lütfen doğru bir kullanıcı adı ve şifre girin.',
        'inactive': 'Bu hesap aktif değil.',
    }

# Ders, Ünite ve Konu modülleri için formlar
class DersForm(forms.ModelForm):
    """Ders oluşturma/düzenleme formu"""
    class Meta:
        model = Ders
        fields = ['ad', 'kod', 'sinav_turu', 'alt_tur', 'aciklama', 'ikon', 'aktif']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'kod': forms.TextInput(attrs={'class': 'form-control'}),
            'sinav_turu': forms.Select(attrs={'class': 'form-select'}),
            'alt_tur': forms.Select(attrs={'class': 'form-select'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'ikon': forms.TextInput(attrs={'class': 'form-control'}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class UniteForm(forms.ModelForm):
    """Ünite oluşturma/düzenleme formu"""
    class Meta:
        model = Unite
        fields = ['ad', 'ders', 'sira_no', 'aciklama', 'aktif']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'ders': forms.Select(attrs={'class': 'form-select'}),
            'sira_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

class KonuForm(forms.ModelForm):
    """Konu oluşturma/düzenleme formu"""
    class Meta:
        model = Konu
        fields = ['ad', 'unite', 'sira_no', 'aciklama', 'aktif']
        widgets = {
            'ad': forms.TextInput(attrs={'class': 'form-control'}),
            'unite': forms.Select(attrs={'class': 'form-select'}),
            'sira_no': forms.NumberInput(attrs={'class': 'form-control'}),
            'aciklama': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'aktif': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

# Profil güncelleme formu
class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False, label="Adınız",
                                 widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Adınız'}))
    last_name = forms.CharField(max_length=150, required=False, label="Soyadınız",
                                widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Soyadınız'}))
    email = forms.EmailField(required=False, label="E-posta Adresi",
                             widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'E-posta Adresi'}))
    date_of_birth = forms.DateField(required=False, label="Doğum Tarihi",
                                    widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}))

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'phone_number', 'date_of_birth']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Telefon Numarası'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # User modelinden alanları forma ekle
        if self.instance and self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        # UserProfile objesini kaydet
        user_profile = super().save(commit=True)

        # User objesini güncelle ve kaydet
        user = user_profile.user
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()

        return user_profile 