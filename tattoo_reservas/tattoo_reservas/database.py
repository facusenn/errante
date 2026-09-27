"""Instancia compartida de SQLAlchemy, desacoplada de la app.

Mantener `db` separado permite crear la app (y cambiar la URI a Postgres)
sin tocar los modelos.
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
