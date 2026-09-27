"""Sync con Google Calendar vía cuenta de servicio (opcional).

Si no hay credenciales configuradas, `is_configured()` devuelve False y la
app sigue funcionando sin calendar — el resto del código nunca asume que
la integración esté activa.
"""
import json
import logging
import os
from datetime import datetime, timedelta

log = logging.getLogger(__name__)

SESSION_HOURS = 3  # duración estimada del turno para el evento


def is_configured():
    return bool(os.environ.get('GOOGLE_SERVICE_ACCOUNT_JSON') and os.environ.get('GOOGLE_CALENDAR_ID'))


def _timezone():
    return os.environ.get('TIMEZONE', 'America/Argentina/Buenos_Aires')


def _credentials():
    raw = os.environ['GOOGLE_SERVICE_ACCOUNT_JSON'].strip()
    if os.path.isfile(raw):
        with open(raw, encoding='utf-8') as f:
            info = json.load(f)
    else:
        info = json.loads(raw)  # el JSON pegado en una sola línea
    from google.oauth2 import service_account
    return service_account.Credentials.from_service_account_info(
        info, scopes=['https://www.googleapis.com/auth/calendar']
    )


def _service():
    from googleapiclient.discovery import build
    return build('calendar', 'v3', credentials=_credentials(), cache_discovery=False)


def check_availability(day, hour):
    """True = el horario está libre, False = ocupado, None = no se pudo verificar."""
    try:
        service = _service()
        tz = _timezone()
        start = datetime.fromisoformat(f'{day.isoformat()}T{hour}')
        end = start + timedelta(hours=SESSION_HOURS)
        result = service.events().list(
            calendarId=os.environ['GOOGLE_CALENDAR_ID'],
            timeMin=start.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            timeZone=tz,
            orderBy='startTime',
        ).execute()
        return len(result.get('items', [])) == 0
    except Exception as e:
        log.warning('check_availability falló: %s', e)
        return None


def create_event(reserva):
    """Crea el evento del turno y devuelve el event_id. Levanta RuntimeError si falla."""
    try:
        service = _service()
        tz = _timezone()
        start = datetime.fromisoformat(f'{reserva.fecha.isoformat()}T{reserva.hora}')
        end = start + timedelta(hours=SESSION_HOURS)
        body = {
            'summary': f'Turno — {reserva.nombre}',
            'description': (
                f'Estilo: {reserva.estilo}\n'
                f'Zona: {reserva.zona} · Tamaño: {reserva.tamano}\n'
                f'Tel: {reserva.telefono} · Email: {reserva.email}'
            ),
            'start': {'dateTime': start.isoformat(), 'timeZone': tz},
            'end': {'dateTime': end.isoformat(), 'timeZone': tz},
        }
        event = service.events().insert(
            calendarId=os.environ['GOOGLE_CALENDAR_ID'], body=body
        ).execute()
        return event['id']
    except Exception as e:
        log.warning('create_event falló: %s', e)
        raise RuntimeError(f'Google Calendar: {e}') from e
