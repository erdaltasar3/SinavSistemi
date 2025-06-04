from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from yks.models import Hatirlatici
from django.contrib.auth.models import User # Kullanıcı modeline erişmek için

class Command(BaseCommand):
    help = 'Sends email reminders for upcoming or past due reminders.'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        # Zamanı gelen ve henüz gönderilmemiş hatırlatıcıları bul
        reminders_to_send = Hatirlatici.objects.filter(
            hatirlatma_tarihi__lte=now,
            sent=False
        ).select_related('kullanici') # Kullanıcı bilgisine daha verimli erişmek için

        self.stdout.write(f'Zamanı gelen {reminders_to_send.count()} hatırlatıcı bulundu.')

        sent_count = 0
        failed_count = 0

        for reminder in reminders_to_send:
            user_email = reminder.kullanici.email
            subject = reminder.baslik
            message = reminder.aciklama if reminder.aciklama else "Hatırlatıcınızın içeriği bulunmamaktadır."

            if not user_email:
                self.stdout.write(self.style.WARNING(f'Kullanıcı {reminder.kullanici.username} için e-posta adresi tanımlı değil. Hatırlatıcı ID: {reminder.id}'))
                failed_count += 1
                continue

            try:
                # E-posta gönderme işlemi
                send_mail(
                    subject, # Konu
                    message, # İçerik
                    settings.EMAIL_HOST_USER, # Gönderen
                    [user_email], # Alıcı listesi
                    fail_silently=False, # Hata durumunda istisna fırlat
                )
                
                # E-posta başarıyla gönderildi, hatırlatıcıyı işaretle
                reminder.sent = True
                reminder.save()
                self.stdout.write(self.style.SUCCESS(f'Hatırlatıcı ID {reminder.id} ({reminder.baslik}) kullanıcısı {reminder.kullanici.username} ({user_email}) adresine gönderildi.'))
                sent_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Hatırlatıcı ID {reminder.id} ({reminder.baslik}) gönderilirken hata oluştu: {e}'))
                failed_count += 1

        self.stdout.write(f'\nToplam: {len(reminders_to_send)}, Gönderilen: {sent_count}, Başarısız: {failed_count}')

        if len(reminders_to_send) > 0 and sent_count == 0:
             self.stdout.write(self.style.ERROR("Hiç hatırlatıcı gönderilemedi. SMTP ayarlarınızı kontrol edin."))
        elif sent_count > 0:
             self.stdout.write(self.style.SUCCESS("Tüm uygun hatırlatıcılar için e-postalar gönderildi."))
        else:
             self.stdout.write("Gönderilecek hatırlatıcı bulunmamaktadır.") 