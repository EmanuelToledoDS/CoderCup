# Faro — Detector de seguridad digital para chicos y adolescentes

Proyecto para CoderCup T1. Buscador que indica la edad recomendada y el
nivel de riesgo de apps/webs, combinando una base de datos curada
manualmente con un fallback de análisis por IA (API de Anthropic).

## Marco de referencia

Base de datos curada con Common Sense Media, App Store/Play Store, ESRB.
Inspirado en el mandato de la Ley 27.576 (modif. Ley 26.061) sobre
interfaces digitales de protección a la niñez, y en la Convención sobre
los Derechos del Niño (jerarquía constitucional, art. 75 inc. 22 CN).

## Correr en local

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # completar ANTHROPIC_API_KEY (opcional)
python manage.py migrate
python manage.py seed_apps
python manage.py runserver
```

Abrir http://localhost:8000. El admin de Django (`/admin/`) permite
editar apps y factores de riesgo sin tocar código — crear superusuario
con `python manage.py createsuperuser`.

## Deploy en Render

1. Subir este repo a GitHub.
2. En Render: New → Blueprint → conectar el repo (usa `render.yaml`).
3. Cargar la variable de entorno `ANTHROPIC_API_KEY` en el dashboard
   de Render (Environment → Add Environment Variable). Sin esto, el
   fallback de IA muestra un error controlado pero el resto de la app
   funciona igual.

## Estructura

- `detector/models.py` — App, FactorRiesgo, Busqueda
- `detector/services.py` — llamada a la API de Anthropic (fallback IA)
- `detector/management/commands/seed_apps.py` — carga las 30 apps base
- `templates/detector/` — UI (Tailwind CDN + HTMX)

## Si cambiás clases de Tailwind

El CSS ya viene compilado en `detector/static/detector/css/tailwind.css`.
Si agregás clases nuevas en los templates, recompilar con:

```bash
npm install -D tailwindcss@3 htmx.org@1.9.10
npx tailwindcss -i ./input.css -o ./detector/static/detector/css/tailwind.css --minify
```
