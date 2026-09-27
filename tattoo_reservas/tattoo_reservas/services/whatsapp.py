"""Confirmación por WhatsApp vía Twilio (opcional).

Sin credenciales de Twilio la app sigue andando: los botones de la UI
usan `wa_me_link()` como fallback, que abre el chat del estudio con un
mensaje pre-escrito.
"""
import logging
import os
import re
from urllib.parse import quote

log = logging.getLogger(__name__)


def is_configured():
    return bool(
        os.environ.get('TWILIO_ACCOUNT_SID')
        and os.environ.get('TWILIO_AUTH_TOKEN')
        and os.environ.get('TWILIO_WHATSAPP_FROM')
    )


def normalize_phone(phone):
    """Devuelve solo dígitos con código de país, o None si está vacío."""
    digits = re.sub(r'\D', '', phone or '')
    return digits or None


def studio_number():
    """Número del estudio para los links wa.me (sin '+' ni espacios)."""
    raw = os.environ.get('WHATSAPP_STUDIO_NUMBER', '')
    return re.sub(r'\D', '', raw)


def wa_me_link(phone=None, text=None):
    """Link de WhatsApp con mensaje pre-escrito.

    `phone` vacío usa el número del estudio (fallback cuando Twilio
    no está configurado).
    """
    target = normalize_phone(phone) or studio_number()
    if not target:
        return None
    url = f'https://wa.me/{target}'
    if text:
        url += f'?text={quote(text)}'
    return url


def send_confirmation(reserva):
    """Envía el mensaje de confirmación al cliente. Devuelve True si se envió."""
    try:
        from twilio.rest import Client
        if not is_configured():
            return False
        target = normalize_phone(reserva.telefono)
        if not target:
            return False
        client = Client(os.environ['TWILIO_ACCOUNT_SID'], os.environ['TWILIO_AUTH_TOKEN'])
        fecha = reserva.fecha.strftime('%d/%m/%Y')
        body = (
            f'¡Hola {reserva.nombre}! Tu turno en Ink.Studio quedó confirmado '
            f'para el {fecha} a las {reserva.hora}. '
            f'Estilo: {reserva.estilo}. Si necesitás cambiar algo, respondé este mensaje.'
        )
        message = client.messages.create(
            from_=f"whatsapp:{os.environ['TWILIO_WHATSAPP_FROM'].lstrip('+')}",
            to=f'whatsapp:+{target.lstrip("+")}',
            body=body,
        )
        log.info('WhatsApp enviado a %s (sid=%s)', reserva.telefono, message.sid)
        return True
    except Exception as e:
        log.warning('send_confirmation falló: %s', e)
        return False


def confirmation_message(reserva):
    fecha = reserva.fecha.strftime('%d/%m/%Y')
    return f'Hola! Confirmame por favor el turno para el {fecha} a las {reserva.hora}. ¡Gracias!'
