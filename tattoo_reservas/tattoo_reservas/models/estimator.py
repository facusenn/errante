from datetime import datetime

from database import db


class EstimatorConfig(db.Model):
    """Configuración del presupuestador editable desde el panel.

    Cada fila es una regla (clave/valor). El valor se guarda como JSON,
    así agregar reglas nuevas no requiere migrar el esquema.
    """
    __tablename__ = 'estimator_config'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<EstimatorConfig {self.key}={self.value}>'
