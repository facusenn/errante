from datetime import datetime

from database import db


class Reserva(db.Model):
    """Turno reservado por un cliente."""
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    fecha = db.Column(db.Date, nullable=False)
    hora = db.Column(db.String(10), nullable=False)
    estilo = db.Column(db.String(50), nullable=False)
    zona = db.Column(db.String(50), nullable=False)
    tamano = db.Column(db.String(30), nullable=False)
    descripcion = db.Column(db.Text)
    es_primera_vez = db.Column(db.Boolean, default=False)
    estado = db.Column(db.String(20), default='pendiente')  # pendiente / confirmado / cancelado
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    # ── Ampliación: vínculo con presupuesto e integraciones ──
    quote_id = db.Column(db.Integer, db.ForeignKey('quote_request.id'))
    calendar_event_id = db.Column(db.String(200))
    calendar_synced_at = db.Column(db.DateTime)
    calendar_status = db.Column(db.String(20), default='pendiente')  # pendiente / sincronizado / conflicto / error
    whatsapp_status = db.Column(db.String(20), default='pendiente')   # pendiente / enviado / wa_me / error
    availability_checked = db.Column(db.Boolean, default=False)

    quote = db.relationship('QuoteRequest', backref='reservas')

    def __repr__(self):
        return f'<Reserva {self.nombre} - {self.fecha}>'
