from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import Hatirlatici
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def send_reminder_email(self, reminder_id):
    """
    Belirli bir hatırlatıcı için e-posta gönderir.
    
    Args:
        reminder_id (int): Hatırlatıcı ID'si
    """
    try:
        # Başlangıç logu
        logger.info(f"📬 Hatırlatıcı e-postası gönderiliyor (ID: {reminder_id})")
        print(f"📬 Hatırlatıcı e-postası gönderiliyor (ID: {reminder_id})")
        
        # Hatırlatıcıyı veritabanından al
        reminder = Hatirlatici.objects.get(id=reminder_id)
        
        # Hatırlatıcı durumunu kontrol et
        if not reminder.aktif:
            logger.info(f"⏭️ Hatırlatıcı pasif durumda, e-posta gönderilmedi (ID: {reminder_id})")
            print(f"⏭️ Hatırlatıcı pasif durumda, e-posta gönderilmedi (ID: {reminder_id})")
            return {
                'status': 'skipped', 
                'reason': 'inactive',
                'reminder_id': reminder_id
            }
        
        # Hatırlatıcının zaten gönderilip gönderilmediğini kontrol et
        if reminder.sent:
            logger.info(f"⏭️ Hatırlatıcı zaten gönderilmiş (ID: {reminder_id})")
            print(f"⏭️ Hatırlatıcı zaten gönderilmiş (ID: {reminder_id})")
            return {
                'status': 'skipped', 
                'reason': 'already_sent',
                'reminder_id': reminder_id
            }
        
        # Kullanıcının e-posta adresini kontrol et
        user_email = reminder.kullanici.email
        if not user_email:
            logger.error(f"❌ Kullanıcının e-posta adresi bulunamadı (ID: {reminder_id})")
            print(f"❌ Kullanıcının e-posta adresi bulunamadı (ID: {reminder_id})")
            return {
                'status': 'error', 
                'reason': 'no_email',
                'reminder_id': reminder_id
            }
        
        # E-posta içeriğini hazırla
        subject = f"Hatırlatıcı: {reminder.baslik}"
        message_body = reminder.aciklama if reminder.aciklama else "Hatırlatıcınız için bildirim."
        message = f"""
Merhaba {reminder.kullanici.username},

Bu bir otomatik hatırlatıcı bildirimdir.

BAŞLIK: {reminder.baslik}
AÇIKLAMA: {message_body}

Hatırlatma Zamanı: {reminder.hatirlatma_tarihi.strftime('%d.%m.%Y %H:%M')}

Sınav Sistemini kullandığınız için teşekkür ederiz.
        """
        
        # E-posta gönder
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user_email],
            fail_silently=False,
        )
        
        # Başarı durumunda hatırlatıcıyı güncelle
        reminder.sent = True
        reminder.save()
        
        logger.info(f"✅ Hatırlatıcı e-postası başarıyla gönderildi (ID: {reminder_id})")
        print(f"✅ Hatırlatıcı e-postası başarıyla gönderildi (ID: {reminder_id})")
        
        return {
            'status': 'success',
            'reminder_id': reminder_id,
            'sent_at': timezone.now().isoformat()
        }
        
    except Hatirlatici.DoesNotExist:
        logger.error(f"❌ Hatırlatıcı bulunamadı (ID: {reminder_id})")
        print(f"❌ Hatırlatıcı bulunamadı (ID: {reminder_id})")
        return {'status': 'error', 'reason': 'not_found', 'reminder_id': reminder_id}
        
    except Exception as e:
        logger.error(f"❌ Hatırlatıcı e-postası gönderilirken hata oluştu (ID: {reminder_id}): {str(e)}")
        print(f"❌ Hatırlatıcı e-postası gönderilirken hata oluştu (ID: {reminder_id}): {str(e)}")
        return {'status': 'error', 'reason': str(e), 'reminder_id': reminder_id} 