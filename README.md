# Radar Digital — Análisis de riesgo digital para chicos y adolescentes

Proyecto para CoderCup T1. Buscador que indica la edad recomendada y el
nivel de riesgo de apps/webs, combinando una base de datos curada
manualmente con un fallback de análisis por IA (API de Groq).

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
cp .env.example .env       # completar GROQ_API_KEY (opcional)
python manage.py migrate
python manage.py seed_apps
python manage.py runserver
```

Abrir http://localhost:8000. El admin de Django (`/admin/`) permite
editar apps y factores de riesgo sin tocar código — crear superusuario
con `python manage.py createsuperuser`.

## Deploy en Render

1. Subir este repo a GitHub.
2. En Render: New → Web Service → conectar el repo → plan Free.
3. Build Command:
   `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate && python manage.py seed_apps`
4. Start Command: `gunicorn config.wsgi:application`
5. Cargar la variable de entorno `GROQ_API_KEY` (Environment → Add
   Environment Variable, key gratis en console.groq.com/keys). Sin
   esto, el fallback de IA muestra un error controlado pero el resto
   de la app funciona igual.

## IA: cómo funciona el ahorro de tokens

Cuando la IA analiza una app que no está en la base curada, el
resultado se guarda automáticamente como un registro nuevo (marcado
`fuente: IA`). La próxima búsqueda del mismo nombre lo encuentra
directo en la base, sin volver a llamar a la IA. En Render free tier
la base SQLite se reinicia en cada redeploy (disco efímero), así que
este ahorro dura mientras no hagas push de nuevo.

## Estructura

- `detector/models.py` — App, FactorRiesgo, Busqueda
- `detector/services.py` — llamada a la API de Groq (fallback IA)
- `detector/views.py` — búsqueda, sugerencias "¿quisiste decir?", análisis IA
- `detector/management/commands/seed_apps.py` — carga las 30 apps base
- `templates/detector/` — UI (Tailwind compilado local + HTMX)

## Si cambiás clases de Tailwind

El CSS ya viene compilado en `detector/static/detector/css/tailwind.css`.
Si agregás clases nuevas en los templates, recompilar con:

```bash
npm install -D tailwindcss@3 htmx.org@1.9.10
npx tailwindcss -i ./input.css -o ./detector/static/detector/css/tailwind.css --minify
```