# Ink.Studio — imagen de producción
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dependencias primero para aprovechar el cache de build
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código de la app
COPY . .

# Directorios de datos (montados como volúmenes en compose) y usuario sin root
RUN mkdir -p uploads/portfolio/thumbs uploads/quotes instance \
 && useradd --create-home appuser \
 && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# init_db() corre al importar app: crea tablas y siembra la config del estimador.
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--timeout", "120", "app:app"]
