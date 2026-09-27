# Ink.Studio — tattoo_reservas

Web de estudio de tatuajes: **portfolio visual**, **presupuestador automático**,
**agenda de turnos** y **panel admin** — todo en Flask + SQLAlchemy, empaquetado
en Docker.

La app funciona **sin ninguna credencial externa**: el portfolio, el
presupuestador, las reservas y el panel admin andan con SQLite local. Las
integraciones (WhatsApp y Google Calendar) se activan solo si se configuran.

---

## Características

- **Portfolio público** — galería masonry responsive con lazy loading y
  miniaturas optimizadas (Pillow). Filtrable por categoría.
- **Presupuestador online** — el cliente elige tamaño y zona y ve el estimado
  en vivo (JS refleja la misma lógica que el backend). Puede subir hasta 3
  fotos de referencia. El estimado es orientativo; el precio final lo cierra
  el tatuador.
- **Panel admin con contraseña** — una sola clave (`ADMIN_PASSWORD`, texto
  plano o hash de werkzeug). Bloqueo tras 5 intentos fallidos.
  - Reservas: filtrar, confirmar, cancelar, eliminar.
  - Presupuestos: revisar referencias, aprobar / rechazar / agendar.
  - Portfolio: subir fotos, editar título / categoría / alt, reordenar, borrar.
  - Precios: base por tamaño, multiplicador por zona y mínimo de sesión —
    guardados en la base, sin tocar código.
  - Excel: export con hojas de Turnos, Presupuestos y Resumen.
- **Flujo presupuesto → turno** — al aprobar un presupuesto, el botón
  *Agendar* abre el formulario de reserva con los datos ya cargados.
- **Integraciones con degradación elegante**
  - Google Calendar (cuenta de servicio): al confirmar un turno verifica el
    horario y crea el evento.
  - WhatsApp (Twilio): envía la confirmación al cliente; sin Twilio, botón
    `wa.me` de fallback.

---

## Estructura

```
tattoo_reservas/
├── app.py                  # composición: config, blueprints, init_db
├── database.py             # db = SQLAlchemy() (listo para Postgres)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── models/                 # Reserva, PortfolioImage, QuoteRequest, QuoteImage, EstimatorConfig
├── services/
│   ├── estimator.py        # lógica de precios (misma para backend y JS)
│   ├── images.py            # Pillow: optimización + miniaturas + borrado seguro
│   ├── google_calendar.py  # opcional — cuenta de servicio
│   └── whatsapp.py         # opcional — Twilio + fallback wa.me
├── routes/
│   ├── public.py           # landing, portfolio, presupuesto, reservas, /uploads
│   └── admin.py            # panel protegido con ADMIN_PASSWORD
├── templates/              # Jinja2 (base + páginas públicas + admin)
├── static/css|js
├── uploads/                # imágenes (volumen Docker) — se crea sola
└── instance/               # SQLite (volumen Docker) — se crea sola
```

---

## Cómo correrlo

### Con Docker (recomendado)

```bash
cd tattoo_reservas
cp .env.example .env        # editá al menos ADMIN_PASSWORD y SECRET_KEY
docker compose up --build
```

→ <http://localhost:5000> · El panel admin vive en <http://localhost:5000/admin>

La base SQLite y las imágenes quedan en `./instance` y `./uploads`
(volúmenes montados), así que sobreviven rebuilds y reinicios.

> Sin `.env` la app arranca igual; el panel queda bloqueado hasta que
> definas `ADMIN_PASSWORD`.

### Sin Docker (desarrollo)

```bash
cd tattoo_reservas
python -m venv .venv
.venv\Scripts\activate          # Windows (bash: source .venv/bin/activate)
pip install -r requirements.txt
python app.py                   # → http://127.0.0.1:5000
```

Al primer arranque se crean las tablas y se siembran los precios por defecto
del estimador.

---

## Configuración — `.env`

Copiá `.env.example` a `.env`. Nada queda hardcodeado en el código.

| Variable | Obligatoria | Descripción |
|---|---|---|
| `SECRET_KEY` | Producción | Firma las sesiones del panel. |
| `ADMIN_PASSWORD` | Para usar el panel | Clave del admin. Texto plano o hash de werkzeug (`pbkdf2:` / `scrypt:`). |
| `DATABASE_URL` | No | Default SQLite. Para Postgres: `postgresql+psycopg://usuario:clave@host:5432/tattoo`. |
| `UPLOAD_FOLDER` | No | Carpeta de imágenes (default `./uploads`). |
| `MAX_CONTENT_MB` | No | Límite de subida, default 8 MB. |
| `TIMEZONE` | No | Para eventos de Calendar. Default `America/Argentina/Buenos_Aires`. |

### Twilio (WhatsApp) — opcional

| Variable | Descripción |
|---|---|
| `TWILIO_ACCOUNT_SID` | SID de la cuenta Twilio. |
| `TWILIO_AUTH_TOKEN` | Token de la cuenta. |
| `TWILIO_WHATSAPP_FROM` | Número del sandbox / remitente (ej. `+14155238886`). |
| `WHATSAPP_STUDIO_NUMBER` | Número del estudio para los links `wa.me` de fallback. |

Sin las tres primeras, al confirmar un turno el panel muestra la opción
“link wa.me”; la app nunca falla por Twilio.

### Google Calendar (cuenta de servicio) — opcional

1. En [Google Cloud Console](https://console.cloud.google.com) creá un
   proyecto y habilitá la **Google Calendar API**.
2. Creá una **cuenta de servicio** y descargá su JSON.
3. En Google Calendar, compartí tu calendario con el email de la cuenta de
   servicio (permiso *Hacer cambios en eventos*).
4. Configurá en `.env`:
   - `GOOGLE_SERVICE_ACCOUNT_JSON` — ruta al archivo JSON descargado **o** el
     JSON completo pegado en una sola línea.
   - `GOOGLE_CALENDAR_ID` — el ID del calendario (suele ser tu email de
     Google, o el de un calendario del estudio).

Sin estas variables, confirmar un turno no toca Calendar (estado “pendiente”).

### Contraseña admin como hash (recomendado)

```bash
python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('tu-clave-secreta'))"
```

El output (`pbkdf2:...` o `scrypt:...`) va en `ADMIN_PASSWORD` del `.env`.

---

## Migración a Postgres (producción / hosting)

1. En el hosting creá la base Postgres.
2. En `.env` cambiá solo:
   ```env
   DATABASE_URL=postgresql+psycopg://usuario:clave@host:5432/tattoo
   ```
   (`psycopg2-binary` ya está en requirements — no hay que instalar nada más,
   SQLAlchemy abstrae el dialecto.)
3. Sobre una base vacía, el primer arranque crea todas las tablas con
   `db.create_all()`.
4. Si más adelante agregás columnas, usá Flask-Migrate (ya conectado):
   ```bash
   flask db migrate -m "mensaje"
   flask db upgrade
   ```
5. Subí las imágenes existentes copiando la carpeta `uploads/`.

En PaaS (Railway, Render, Fly.io): apuntá `DATABASE_URL` a su Postgres,
`UPLOAD_FOLDER` a un volumen persistente si el PaaS lo ofrece (si no,
[hay que configurar S3 u otro storage](https://flask.palletsprojects.com/en/stable/patterns/fileuploads/)
— el código guarda todo bajo `UPLOAD_FOLDER`, es el único punto a adaptar).

---

## Precios del estimador

Panel admin → **Precios**. El estimado es:

```
total = base_del_tamaño × multiplicador_de_zona   (mínimo: min_price)
rango  = total × 0.90 … total × 1.15
```

Todos los valores viven en la tabla `estimator_config` y se aplican al
instante en el formulario público (backend y JS leen la misma config).

## Checklist de prueba (smoke test)

1. `docker compose up --build` → abre <http://localhost:5000>.
2. `/portfolio` vacío — sin errores; subí una foto desde `/admin/portfolio`.
3. `/presupuesto`: elegí tamaño + zona → estimado en vivo; envialo sin fotos
   (y con hasta 3 fotos).
4. `/admin`: entrá con `ADMIN_PASSWORD`; aprobá el presupuesto, apretá
   **Agendar turno**, completá la reserva y confirmala.
5. Confirmar un turno sin Twilio/Google → aviso “link wa.me” y calendario
   “pendiente”; el turno queda confirmado igual.
6. `/admin/exportar-excel` baja el xlsx con las tres hojas.
7. **Precios**: cambiá `size_chico`, guardá, y verificá el cambio en
   `/presupuesto`. *Restaurar valores por defecto* los revierte.

---

## Notas de seguridad

- `ADMIN_PASSWORD` nunca se sube al repo (`.env` está ignorado).
- Login con bloqueo de 5 intentos / 5 minutos.
- Borrado de imágenes con guard de path traversal (no puede salir de
  `uploads/`).
- Subidas limitadas a PNG/JPG/WebP y `MAX_CONTENT_MB` por request.
