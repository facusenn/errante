from database import db
from .base import BaseModel


class QuoteRequest(BaseModel):
    """Solicitud de presupuesto enviada desde la web."""
    __tablename__ = 'quote_request'
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30), nullable=False)
    size = db.Column(db.String(20), nullable=False)      # chico / mediano / grande / xl
    zone = db.Column(db.String(50), nullable=False)      # etiqueta de zona (ej: Brazo)
    description = db.Column(db.Text)
    estimated_price = db.Column(db.Float)
    status = db.Column(db.String(20), default='pendiente', nullable=False)  # pendiente / aprobado / rechazado / agendado
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<QuoteRequest {self.id} - {self.nombre}>'


class QuoteImage(BaseModel):
    """Foto de referencia adjunta a un presupuesto."""
    __tablename__ = 'quote_image'
    id = db.Column(db.Integer, primary_key=True)
    quote_id = db.Column(db.Integer, db.ForeignKey('quote_request.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(300), nullable=False)
    original_filename = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    quote = db.relationship('QuoteRequest', backref=db.backref('images', cascade='all, delete-orphan'))
