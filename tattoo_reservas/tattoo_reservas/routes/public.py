"""Rutas públicas: landing, portfolio, presupuestos, reservas y archivos subidos."""
import json
from datetime import datetime

from flask import (Blueprint, current_app, flash, redirect,
                   render_template, request, send_from_directory, url_for)

from database import db
from models import PortfolioImage, QuoteRequest, QuoteImage, Reserva
from services import images
from services import whatsapp
from services.estimator import (SIZE_OPTIONS, ZONE_OPTIONS, estimate_price,
                                get_config)

public_bp = Blueprint('public', __name__)

MAX_QUOTE_PHOTOS = 3


def _quote_js_config():
    """Config del estimador en formato JS-friendly para el preview en vivo."""
    live = get_config()
    sizes = {key: float(live.get(f'size_{key}', 0)) for key, _ in SIZE_OPTIONS}
    zones = {key: float(live.get(f'zone_{key}', 1.0)) for _, key in ZONE_OPTIONS}
    return {
        'min_price': float(live.get('min_price', 0)),
        'sizes': sizes,
        'zones': zones,
    }


def _quote_form_context():
    return {
        'size_options': SIZE_OPTIONS,
        'zone_options': ZONE_OPTIONS,  # (label, key) — el key va en data-key para el JS
        'quote_js_config': json.dumps(_quote_js_config()),
    }


# ─────────────────────────────────────────────
# LANDING
# ─────────────────────────────────────────────

@public_bp.route('/')
def index():
    destacados = PortfolioImage.query.order_by(
        PortfolioImage.sort_order.asc(), PortfolioImage.id.desc()
    ).limit(6).all()
    return render_template('index.html', destacados=destacados)


# ─────────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────────

@public_bp.route('/portfolio')
def portfolio():
    categoria = request.args.get('categoria', '').strip()
    query = PortfolioImage.query.order_by(
        PortfolioImage.sort_order.asc(), PortfolioImage.id.desc()
    )
    if categoria:
        query = query.filter_by(category=categoria)
    fotos = query.all()
    categorias = sorted({
        f.category for f in PortfolioImage.query.with_entities(PortfolioImage.category)
        if f.category
    })
    return render_template('portfolio.html', fotos=fotos,
                           categorias=categorias, categoria_actual=categoria)


# ─────────────────────────────────────────────
# PRESUPUESTOS
# ─────────────────────────────────────────────

@public_bp.route('/presupuesto', methods=['GET', 'POST'])
def presupuesto():
    ctx = _quote_form_context()

    if request.method == 'POST':
        try:
            size = request.form['size']
            zone = request.form['zone']
            calc = estimate_price(size, zone)
        except (KeyError, ValueError) as e:
            flash('Elegí un tamaño y una zona válidos para estimar.', 'error')
            return render_template('presupuesto.html', **ctx)

        fotos_guardadas = []

        try:
            quote = QuoteRequest(
                nombre=request.form['nombre'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                size=size,
                zone=zone,
                description=request.form.get('description', ''),
                estimated_price=calc['total'],
            )
            db.session.add(quote)
            db.session.commit()

            # Fotos de referencia (opcional, hasta 3)
            uploads = [f for f in request.files.getlist('fotos') if f and f.filename]
            for file_storage in uploads[:MAX_QUOTE_PHOTOS]:
                try:
                    relative, _thumb = images.save_image(
                        file_storage, current_app.config['UPLOAD_FOLDER'], 'quotes')
                    db.session.add(QuoteImage(
                        quote_id=quote.id,
                        filename=relative,
                        original_filename=file_storage.filename,
                    ))
                    fotos_guardadas.append(relative)
                except images.ImageError as ie:
                    flash(str(ie), 'error')

            db.session.commit()
            flash('¡Presupuesto enviado! El estimado es orientativo.', 'success')
            return redirect(url_for('public.presupuesto_detail', id=quote.id))

        except Exception as e:
            db.session.rollback()
            flash(f'Error al guardar el presupuesto: {str(e)}', 'error')

    return render_template('presupuesto.html', **ctx)


@public_bp.route('/presupuesto/<int:id>')
def presupuesto_detail(id):
    quote = QuoteRequest.query.get_or_404(id)
    try:
        calc = {
            'range_low': round(quote.estimated_price * 0.90),
            'range_high': round(quote.estimated_price * 1.15),
        }
    except TypeError:
        calc = None
    return render_template('presupuesto_confirm.html', quote=quote, calc=calc)


# ─────────────────────────────────────────────
# RESERVAS (flujo existente + datos del presupuesto)
# ─────────────────────────────────────────────

@public_bp.route('/reservar', methods=['GET', 'POST'])
def reservar():
    quote = None
    quote_id = request.args.get('quote_id', type=int)
    if quote_id:
        quote = QuoteRequest.query.get_or_404(quote_id)
        if quote.status not in ('aprobado', 'agendado'):
            flash('Ese presupuesto todavía no está aprobado.', 'error')
            quote = None

    if request.method == 'POST':
        try:
            nueva = Reserva(
                nombre=request.form['nombre'],
                email=request.form['email'],
                telefono=request.form['telefono'],
                fecha=datetime.strptime(request.form['fecha'], '%Y-%m-%d').date(),
                hora=request.form['hora'],
                estilo=request.form['estilo'],
                zona=request.form['zona'],
                tamano=request.form['tamano'],
                descripcion=request.form.get('descripcion', ''),
                es_primera_vez='es_primera_vez' in request.form,
            )
            if quote is not None:
                nueva.quote_id = quote.id

            db.session.add(nueva)
            db.session.commit()

            if quote is not None:
                quote.status = 'agendado'
                db.session.commit()

            flash('¡Reserva enviada! Te vamos a contactar para confirmar el turno.', 'success')
            return redirect(url_for('public.confirmacion', id=nueva.id))
        except Exception as e:
            flash(f'Error al guardar la reserva: {str(e)}', 'error')

    prefill = {}
    if quote is not None:
        prefill = {
            'nombre': quote.nombre,
            'email': quote.email,
            'telefono': quote.telefono,
            'descripcion': quote.description or '',
        }
    return render_template('reservar.html', quote=quote, prefill=prefill)


@public_bp.route('/confirmacion/<int:id>')
def confirmacion(id):
    reserva = Reserva.query.get_or_404(id)
    wa_link = whatsapp.wa_me_link(
        phone=None, text=f'Hola! Acabo de reservar un turno (#{reserva.id}). Quiero confirmar.'
    ) if whatsapp.studio_number() else None
    return render_template('confirmacion.html', reserva=reserva, wa_link=wa_link)


# ─────────────────────────────────────────────
# ARCHIVOS SUBIDOS
# ─────────────────────────────────────────────

@public_bp.route('/uploads/<path:filename>')
def serve_upload(filename):
    upload_root = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_root, filename)
