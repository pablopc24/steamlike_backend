import os
import requests
from requests.exceptions import Timeout, ConnectionError

class EmailServiceError(Exception):
    """Error genérico del servicio de email."""
    pass

class ExternalServiceUnavailable(EmailServiceError):
    """503 - Fallo de red o timeout."""
    pass

class ExternalServiceError(EmailServiceError):
    """502 - Error del proveedor."""
    pass


class EmailService:
    def __init__(self):
        self.token = os.getenv("MAILEROO_TOKEN")
        self.from_address = os.getenv("MAILEROO_FROM")
        self.endpoint = os.getenv("MAILEROO_ENDPOINT", "https://smtp.maileroo.com/api/v2/emails")
        self.timeout = int(os.getenv("MAILEROO_TIMEOUT", 5))

    def send_email(self, to, subject, text, html=None):
        payload = {
            "from": {
                "address": self.from_address,
                "display_name": "SteamLike"
            },
            "to": [
                {
                    "address": to,
                    "display_name": "Usuario"
                }
            ],
            "subject": subject,
            "plain": text,
            "text": text,
        }

        if html:
            payload["html"] = html

        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-API-Key": self.token,
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(
                self.endpoint,
                json=payload,
                headers=headers,
                timeout=self.timeout
            )

        except (Timeout, ConnectionError):
            raise ExternalServiceUnavailable("external_service_unavailable")

        # Si Maileroo responde con error
        if not response.ok:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Maileroo error: {response.status_code} - {response.text}")
            raise ExternalServiceError("external_service_error")

        # Si Maileroo devuelve algo inesperado
        try:
            data = response.json()
        except ValueError:
            raise ExternalServiceError("external_service_error")

        return data
