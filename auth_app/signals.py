import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from catalog.services.email_service import (
    EmailService,
    ExternalServiceUnavailable,
    ExternalServiceError
)

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if not created:
        return

    logger.info(f"Intento de envo de email de bienvenida a {instance.username}")
    
    service = EmailService()
    try:
        service.send_email(
            to=instance.username,  # Asumiendo que username es el email o se usa como tal
            subject="Bienvenido a SteamLike",
            text="Tu cuenta ha sido creada correctamente."
        )
        logger.info(f"[EMAIL OK] Email de bienvenida enviado a {instance.username}")
        
    except ExternalServiceUnavailable:
        logger.error(f"[EMAIL ERROR 503] Fallo de red enviando email a {instance.username}")
        
    except ExternalServiceError:
        logger.error(f"[EMAIL ERROR 502] Error del proveedor enviando email a {instance.username}")
        
    except Exception as e:
        logger.error(f"[EMAIL ERROR] Error inesperado enviando email a {instance.username}: {str(e)}")
