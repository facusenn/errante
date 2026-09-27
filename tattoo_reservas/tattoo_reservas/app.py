"""Ink.Studio — app Flask: portfolio, presupuestador y agenda de turnos.

Punto de ensamblado: crea la app, carga la config desde .env, registra
los blueprints y prepara la base (SQLite por defecto, Postgres cambiando
solo DATABASE_URL).
"""
import logging
import os
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask
from flask_migrate import Migrate

from database import db
from models import EstimatorConfig, PortfolioImage, QuoteRequest, Reserva  # noqa: F401 (create_all)
from routes.admin import admin_bp
from routes.public import public_bp
from services.estimator import seed_defaults
from services.images import ensure_upload_dirs

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-cambia-esta-clave-en-produccion')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL')
    or 'sqlite:///' + os.path.join(app.instance_path, 'reservas.db')
)
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER') or os.path.join(BASE_DIR, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = int(os.environ.get('MAX_CONTENT_MB', '8')) * 1024 * 1024

db.init_app(app)
migrate = Migrate(app, db)

os.makedirs(app.instance_path, exist_ok=True)
ensure_upload_dirs(app.config['UPLOAD_FOLDER'])

app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)


@app.context_processor
def inject_globals():
    return {'current_year': datetime.now().year}


def _ensure_sqlite_columns():
    """Actualiza la base SQLite existente si le faltan columnas nuevas.

    Solo para SQLite en desarrollo: agrega por ALTER TABLE las columnas
    que la ampliación necesita. Para Postgres usar `flask db migrate`.
    """
    if db.engine.dialect.name != 'sqlite':
        return
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if 'reserva' not in inspector.get_table_names():
        return
    existing = {c['name'] for c in inspector.get_columns('reserva')}
    new_columns = {
        'quote_id': 'INTEGER',
        'calendar_event_id': 'VARCHAR(200)',
        'calendar_synced_at': 'DATETIME',
        'calendar_status': "VARCHAR(20) DEFAULT 'pendiente'",
        'whatsapp_status': "VARCHAR(20) DEFAULT 'pendiente'",
        'availability_checked': 'BOOLEAN DEFAULT 0',
    }
    added = False
    for column, ddl in new_columns.items():
        if column not in existing:
            db.session.execute(text(f'ALTER TABLE reserva ADD COLUMN {column} {ddl}'))
            added = True
    if added:
        db.session.commit()
        logging.info('SQLite: columnas agregadas a reserva para la ampliación.')


def init_db():
    """Crea tablas nuevas, actualiza la base dev y siembra la config del estimador."""
    with app.app_context():
        db.create_all()
        _ensure_sqlite_columns()
        seed_defaults()


init_db()

if __name__ == '__main__':
    app.run(debug=True)
