from database import db
from .base import BaseModel


class PortfolioImage(BaseModel):
    """Foto de un tatuaje realizado, para la galería pública."""
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(300), nullable=False, unique=True)
    thumb_filename = db.Column(db.String(300), nullable=False)
    title = db.Column(db.String(150))
    category = db.Column(db.String(50))   # estilo o zona del cuerpo
    alt_text = db.Column(db.String(200))
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PortfolioImage {self.id} - {self.title}>'
