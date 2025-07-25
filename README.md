# 🎓 Sınav Sistemi - YKS Hazırlık Platformu

![](https://img.shields.io/badge/Django-4.2.22-green.svg)
![](https://img.shields.io/badge/Bootstrap-5-blue.svg)
![](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)
![](https://img.shields.io/badge/Celery-5.3.4-brightgreen.svg)

## 📋 Proje Tanımı

Sınav Sistemi, öğrencilerin YKS ve diğer merkezi sınavlara hazırlanmasını kolaylaştıran kapsamlı bir web platformudur. Konu takibi, çalışma planlaması, hedef belirleme ve ilerleme analizi gibi çeşitli araçlar sunarak öğrencilerin verimli çalışmasına yardımcı olur.

## ✨ Özellikler

- 📚 **Sınav ve Ders Yönetimi:** TYT, AYT ve YDT oturumları için detaylı konu takibi
- 📝 **Konu Takip Sistemi:** Çalışılan konuları işaretleme ve ilerleme analizi
- 🎯 **Hedef Belirleme:** Günlük, haftalık ve aylık çalışma hedefleri oluşturma
- 📊 **Deneme Analizi:** Deneme sınavı sonuçlarını kaydetme ve analiz etme
- ⏰ **Çalışma Planlaması:** Günlük, haftalık çalışma planları oluşturma
- ⏱️ **Pomodoro Zamanlayıcı:** Verimli çalışma için zamanlayıcı
- 📧 **Otomatik Hatırlatıcılar:** E-posta ile çalışma hatırlatmaları
- 👤 **Kullanıcı Profili:** Kişiselleştirilmiş öğrenci profili

## 🛠️ Teknolojiler

- **Backend:** Django 4.2.22
- **Frontend:** Bootstrap 5, JavaScript
- **Veritabanı:** PostgreSQL
- **Asenkron Görevler:** Celery
- **Kimlik Doğrulama:** Django Authentication
- **E-posta:** SMTP (Gmail)
- **Form İşleme:** Crispy Forms + Bootstrap5

## 🚀 Kurulum

1. Repoyu klonlayın:
   ```bash
   git clone https://github.com/username/SinavSistemi.git
   cd SinavSistemi
   ```

2. Bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

3. Veritabanını kurun:
   ```bash
   python manage.py migrate
   ```

4. Geliştirme sunucusunu başlatın:
   ```bash
   python manage.py runserver
   ```

5. Celery worker'ı başlatın:
   ```bash
   celery -A SinavSistemi worker --loglevel=info
   ```

6. Tarayıcınızda [http://localhost:8000](http://localhost:8000) adresine gidin

## 📷 Ekran Görüntüleri

# 1-) Kayıt Ol ve Giriş Yap 

![Kayıt Ol](static/images/5.png)
![Giriş Yap](static/images/4.png)

# 2-) YKS Modüller Sayfası
   ![Modüller](static/images/6.png)
   
# 3-) Konu Takip Sistemi
   ![Konu Takip Sistemi](static/images/7.png)
   ![Konu Takip Sistemi](static/images/8.png)
   
# 4-) Hedeflerim
   ![Hedeflerim](static/images/9.png)

# 4-) Çalışma Planı
   ![Çalışma Planı](static/images/10.png)

# 5-) Denemelerim
   ![Denemelerim](static/images/11.png)

# 6-) Geliştirme Aşamasındaki Modül Ekranları
   ![Geliştirme Aşaması](static/images/12.png)
   
## 🗂️ Proje Yapısı

- **core:** Temel sistem bileşenleri, kullanıcı yönetimi
- **yks:** YKS sınavına özel modüller ve işlevler
- **static:** CSS, JavaScript, resimler
- **templates:** HTML şablonları
- **media:** Kullanıcı yüklenen dosyalar

## 📝 Lisans

Bu proje [MIT Lisansı](LICENSE) altında lisanslanmıştır.

## 📞 İletişim

Sorularınız veya önerileriniz için: [erdaltasar24@gmail.com](mailto:erdaltasar24@gmail.com)

---

⭐ Bu projeyi beğendiyseniz, yıldız vermeyi unutmayın! ⭐
