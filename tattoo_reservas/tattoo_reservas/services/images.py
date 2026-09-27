"""Guardado y optimización de imágenes subidas (Pillow).

Cada imagen se guarda como JPEG optimizado (máx. 2000 px) más una
miniatura (máx. 480 px) dentro de subcarpetas de UPLOAD_FOLDER.
"""
import os
import uuid

from PIL import Image, ImageOps
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
MAX_ORIGINAL = 2000     # px, lado más largo
THUMB_SIZE = (480, 480)
JPEG_QUALITY_ORIGINAL = 88
JPEG_QUALITY_THUMB = 80


class ImageError(Exception):
    pass


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _slug(name):
    base = secure_filename(os.path.splitext(name)[0])[:40]
    return base or 'imagen'


def _open_flexible(file_storage):
    """Abre la imagen aplicando rotación EXIF (fotos de celular) y fondo blanco para PNG con transparencia."""
    try:
        img = Image.open(file_storage)
        img = ImageOps.exif_transpose(img)
    except Exception as e:
        raise ImageError(f'No se pudo abrir la imagen: {e}') from e

    if img.mode in ('RGBA', 'LA', 'P'):
        background = Image.new('RGB', img.size, (255, 255, 255))
        img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1])
        img = background
    else:
        img = img.convert('RGB')
    return img


def save_image(file_storage, upload_root, category='portfolio'):
    """Guarda original + miniatura. Devuelve (filename, thumb_filename),
    ambos rutas relativas a UPLOAD_FOLDER."""
    if not file_storage or not file_storage.filename:
        raise ImageError('Archivo vacío')
    if not allowed_file(file_storage.filename):
        raise ImageError(f'Formato no permitido: {file_storage.filename}')

    uid = uuid.uuid4().hex[:10]
    slug = _slug(file_storage.filename)
    name = f'{uid}-{slug}.jpg'

    original_dir = os.path.join(upload_root, category)
    thumb_dir = os.path.join(upload_root, category, 'thumbs')
    os.makedirs(original_dir, exist_ok=True)
    os.makedirs(thumb_dir, exist_ok=True)

    img = _open_flexible(file_storage)

    # Original optimizado
    if max(img.size) > MAX_ORIGINAL:
        img.thumbnail((MAX_ORIGINAL, MAX_ORIGINAL), Image.Resampling.LANCZOS)
    original_path = os.path.join(original_dir, name)
    img.save(original_path, 'JPEG', quality=JPEG_QUALITY_ORIGINAL, optimize=True)

    # Miniatura para la grilla
    thumb = img.copy()
    thumb.thumbnail(THUMB_SIZE, Image.Resampling.LANCZOS)
    thumb_path = os.path.join(thumb_dir, name)
    thumb.save(thumb_path, 'JPEG', quality=JPEG_QUALITY_THUMB, optimize=True)

    return (
        f'{category}/{name}',
        f'{category}/thumbs/{name}',
    )


def remove_image(upload_root, relative_path):
    """Borra un archivo (si existe) del volumen de uploads. Nunca levanta error."""
    if not relative_path:
        return
    absolute = os.path.abspath(os.path.join(upload_root, relative_path))
    upload_root_abs = os.path.abspath(upload_root)
    if os.path.commonpath([absolute, upload_root_abs]) != upload_root_abs:
        return
    try:
        if os.path.exists(absolute):
            os.remove(absolute)
    except OSError:
        pass


def ensure_upload_dirs(root):
    for sub in ('portfolio', 'portfolio/thumbs', 'quotes', 'quotes/thumbs'):
        os.makedirs(os.path.join(root, sub), exist_ok=True)
