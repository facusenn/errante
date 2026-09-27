"""Cálculo de presupuestos: precio base por tamaño × multiplicador por zona.

Todas las reglas viven en la tabla `estimator_config` y son editables
desde el panel admin; `DEFAULT_CONFIG` es solo el punto de partida y el
fallback si falta una clave.
"""
import json

from database import db
from models.estimator import EstimatorConfig

# Opciones que ve el cliente en el formulario público
SIZE_OPTIONS = [
    ('chico',   'Chico (hasta 5 cm)'),
    ('mediano', 'Mediano (5–15 cm)'),
    ('grande',  'Grande (15–25 cm)'),
    ('xl',      'Extra grande (25+ cm)'),
]

ZONE_OPTIONS = [
    ('Brazo', 'brazo'),
    ('Antebrazo', 'antebrazo'),
    ('Mano', 'mano'),
    ('Pecho', 'pecho'),
    ('Espalda', 'espalda'),
    ('Costilla', 'costilla'),
    ('Pierna', 'pierna'),
    ('Tobillo / Pie', 'tobillo_pie'),
    ('Cuello', 'cuello'),
    ('Otro', 'otro'),
]

ZONE_KEYS = {label: key for label, key in ZONE_OPTIONS}
SIZE_LABELS = dict(SIZE_OPTIONS)

# Valores por defecto (ARS). Se siembran la primera vez que arranca la app
# y quedan guardados en la base para que el tatuador los edite.
DEFAULT_CONFIG = {
    'min_price': 15000,

    'size_chico': 18000,
    'size_mediano': 35000,
    'size_grande': 60000,
    'size_xl': 90000,

    'zone_brazo': 1.00,
    'zone_antebrazo': 1.05,
    'zone_mano': 1.15,
    'zone_pecho': 1.10,
    'zone_espalda': 1.20,
    'zone_costilla': 1.25,
    'zone_pierna': 1.00,
    'zone_tobillo_pie': 1.10,
    'zone_cuello': 1.15,
    'zone_otro': 1.00,
}

# Estructura del formulario de configuración del panel
CONFIG_GROUPS = [
    ('Precio base por tamaño (ARS)', [
        ('size_chico', 'Chico'),
        ('size_mediano', 'Mediano'),
        ('size_grande', 'Grande'),
        ('size_xl', 'Extra grande'),
    ]),
    ('Multiplicador por zona (×)', [
        (f'zone_{key}', label) for label, key in ZONE_OPTIONS
    ]),
    ('Mínimo de sesión', [
        ('min_price', 'Precio mínimo de sesión (ARS)'),
    ]),
]


def _parse(raw):
    try:
        return json.loads(raw)
    except (TypeError, ValueError):
        return None


def get_config():
    """Config efectiva: defaults + lo guardado en la base."""
    cfg = dict(DEFAULT_CONFIG)
    for row in EstimatorConfig.query.all():
        parsed = _parse(row.value)
        if parsed is not None:
            cfg[row.key] = parsed
    return cfg


def set_config(key, value):
    row = EstimatorConfig.query.filter_by(key=key).first()
    if row is None:
        row = EstimatorConfig(key=key, value=json.dumps(value))
        db.session.add(row)
    else:
        row.value = json.dumps(value)
    db.session.commit()


def seed_defaults(force=False):
    """Carga los defaults que falten (o todos, si force=True)."""
    for key, value in DEFAULT_CONFIG.items():
        exists = EstimatorConfig.query.filter_by(key=key).first()
        if exists is None or (force and exists is not None):
            if exists is None:
                db.session.add(EstimatorConfig(key=key, value=json.dumps(value)))
            else:
                exists.value = json.dumps(value)
    db.session.commit()


def zone_key(zone):
    """Acepta la etiqueta ('Brazo') o la clave ('brazo') y devuelve la clave."""
    if zone in ZONE_KEYS:
        return ZONE_KEYS[zone]
    if f'zone_{zone}' in DEFAULT_CONFIG:
        return zone
    raise ValueError(f'Zona desconocida: {zone}')


def zone_label(key):
    for label, k in ZONE_OPTIONS:
        if k == key:
            return label
    return key


def size_label(key):
    return SIZE_LABELS.get(key, key)


def estimate_price(size, zone, cfg=None):
    """Calcula el estimado. Devuelve valores redondeados con rango ±10/15%.

    `size` es la clave del tamaño ('chico'…'xl') y `zone` acepta etiqueta o clave.
    """
    cfg = cfg if cfg is not None else get_config()
    if f'size_{size}' not in cfg:
        raise ValueError(f'Tamaño desconocido: {size}')
    zkey = zone_key(zone)

    base = float(cfg.get(f'size_{size}', 0))
    multiplier = float(cfg.get(f'zone_{zkey}', 1.0))
    subtotal = base * multiplier
    minimum = float(cfg.get('min_price', 0))
    min_applied = subtotal < minimum
    total = max(subtotal, minimum)

    return {
        'base_price': round(base),
        'multiplier': multiplier,
        'subtotal': round(subtotal),
        'min_applied': min_applied,
        'total': round(total),
        'range_low': round(total * 0.90),
        'range_high': round(total * 1.15),
    }
