from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Hatirlatici

@shared_task
def send_reminder_email(reminder_id):
    """Belirli bir hatırlatıcı için e-posta gönderir."""
    print(f"DEBUG: Celery task send_reminder_email started for reminder ID: {reminder_id}")
    try:
        reminder = Hatirlatici.objects.get(id=reminder_id)
        
        # Hatırlatıcı zaten gönderilmişse veya tarihi henüz gelmemişse tekrar gönderme
        if reminder.sent or reminder.hatirlatma_tarihi > timezone.now():
            print(f"DEBUG: Reminder ID {reminder_id} already sent or time not yet arrived. Skipping send.")
            print(f"DEBUG: Reminder sent status: {reminder.sent}, Hatırlatma Tarihi: {reminder.hatirlatma_tarihi}, Current Time: {timezone.now()}")
            return

        user_email = reminder.kullanici.email
        subject = reminder.baslik
        message = reminder.aciklama if reminder.aciklama else "Hatırlatıcınızın içeriği bulunmamaktadır."

        if not user_email:
            print(f"DEBUG: No email address defined for user {reminder.kullanici.username}. Reminder ID: {reminder.id}. Skipping send.")
            # Burada loglama yapılabilir veya farklı bir hata yönetimi uygulanabilir
            return

        try:
            # E-posta gönderme işlemi
            print(f"DEBUG: Attempting to send email for reminder ID {reminder.id} to {user_email}")
            send_mail(
                subject, # Konu
                message, # İçerik
                settings.DEFAULT_FROM_EMAIL, # Gönderen (settings.py'deki DEFAULT_FROM_EMAIL)
                [user_email], # Alıcı listesi
                fail_silently=False, # Hata durumunda istisna fırlat
            )
            
            # E-posta başarıyla gönderildi, hatırlatıcıyı işaretle
            reminder.sent = True
            reminder.save()
            print(f"DEBUG: Email successfully sent for reminder ID {reminder.id}. Reminder marked as sent.")

        except Exception as e:
            print(f"DEBUG: Error sending email for reminder ID {reminder.id}: {e}")
            # Hata durumunda loglama yapılabilir.
            # Celery görevleri için otomatik tekrar deneme (retry) ayarları düşünülebilir.

    except Hatirlatici.DoesNotExist:
        print(f"DEBUG: Reminder with ID {reminder_id} not found.")
    except Exception as e:
        print(f"DEBUG: An unexpected error occurred in Celery task for reminder ID {reminder_id}: {e}")

    # Bu satır kaldırılmalı, görev sadece bir kere çalışmalı. apply_async view'de yapılmalı.
    # send_reminder_email.apply_async(args=[reminder.id], eta=reminder.hatirlatma_tarihi) 