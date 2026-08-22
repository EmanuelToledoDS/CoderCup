import hashlib

from django.db.models import Count, Q
from django.shortcuts import render, get_object_or_404
from django.utils.text import slugify
from django.views.decorators.http import require_GET

from .models import App, FactorRiesgo, Busqueda
from .services import analizar_app_con_ia, AIAnalysisError


COLOR_RIESGO = {
    "bajo": "#4ECDC4",
    "medio": "#FFB84D",
    "alto": "#FF6B5B",
    "muy_alto": "#E23B32",
}

MENSAJE_RIESGO = {
    "bajo": "Apta, con supervisión habitual",
    "medio": "Requiere acompañamiento",
    "alto": "No recomendada sin supervisión",
    "muy_alto": "No recomendada para menores",
}


def _guardar_app_analizada(nombre_app, resultado):
    """
    Guarda el resultado de la IA como registro curado (fuente=IA) para que
    la próxima búsqueda del mismo nombre lo encuentre directo en la base,
    sin volver a gastar tokens de IA. Si ya existe un slug igual (carrera
    o app ya cargada), no pisa el registro existente.
    """
    slug = slugify(nombre_app)[:140]
    if App.objects.filter(slug=slug).exists():
        return

    edad = min(max(int(resultado.get("edad_recomendada", 13)), 0), 18)
    nivel = resultado.get("nivel_riesgo") if resultado.get("nivel_riesgo") in dict(
        App.NivelRiesgo.choices
    ) else App.NivelRiesgo.MEDIO

    app = App.objects.create(
        nombre=nombre_app,
        slug=slug,
        descripcion_corta=(resultado.get("justificacion", "")[:280]) or "Análisis generado por IA.",
        edad_recomendada=edad,
        nivel_riesgo=nivel,
        justificacion=resultado.get("justificacion", ""),
        fuente=App.Fuente.IA,
        fuente_detalle="Estimado automáticamente por IA, no verificado manualmente.",
        logo_emoji="🤖",
        activo=True,
    )

    factores_objs = []
    for nombre_factor in resultado.get("factores_riesgo", [])[:5]:
        factor, _ = FactorRiesgo.objects.get_or_create(
            nombre=nombre_factor[:120],
            defaults={
                "descripcion": nombre_factor[:280],
                "categoria": FactorRiesgo.Categoria.CONTENIDO,
            },
        )
        factores_objs.append(factor)
    if factores_objs:
        app.factores.set(factores_objs)


def _hash_ip(request):
    ip = request.META.get("REMOTE_ADDR", "")
    return hashlib.sha256(ip.encode()).hexdigest()[:16]


def _enriquecer_resultado_ia(resultado):
    edad = min(max(int(resultado.get("edad_recomendada", 13)), 0), 18)
    resultado["angulo_dial"] = round((edad / 18) * 180) - 90
    resultado["color_riesgo"] = COLOR_RIESGO.get(resultado.get("nivel_riesgo"), "#FFB84D")
    resultado["mensaje_riesgo"] = MENSAJE_RIESGO.get(resultado.get("nivel_riesgo"), "")
    return resultado


def home(request):
    mas_buscadas = (
        Busqueda.objects.exclude(app_encontrada__isnull=True)
        .values("app_encontrada__nombre", "app_encontrada__slug", "app_encontrada__logo_emoji")
        .annotate(total=Count("id"))
        .order_by("-total")[:6]
    )
    total_apps = App.objects.filter(activo=True).count()
    return render(request, "detector/home.html", {"mas_buscadas": mas_buscadas, "total_apps": total_apps})


@require_GET
def buscar(request):
    query = request.GET.get("q", "").strip()
    if len(query) < 2:
        return render(request, "detector/_resultados.html", {"query": query, "apps": None})
    apps = App.objects.filter(
        Q(nombre__icontains=query) | Q(categoria__icontains=query), activo=True
    ).prefetch_related("factores")[:8]
    return render(request, "detector/_resultados.html", {"query": query, "apps": apps})


@require_GET
def analizar(request):
    query = request.GET.get("q", "").strip()[:60]
    if not query:
        return render(request, "detector/_analisis_ia.html", {"error": "Ingresá un nombre."})

    Busqueda.objects.create(termino=query, resuelta_por_ia=True, ip_hash=_hash_ip(request))

    try:
        resultado = analizar_app_con_ia(query)
    except AIAnalysisError as exc:
        return render(request, "detector/_analisis_ia.html", {"error": str(exc), "query": query})

    if not resultado.get("existe", True):
        return render(request, "detector/_analisis_ia.html", {"no_encontrada": True, "query": query})

    resultado = _enriquecer_resultado_ia(resultado)
    _guardar_app_analizada(query, resultado)
    return render(request, "detector/_analisis_ia.html", {"resultado": resultado, "query": query})


def detalle_app(request, slug):
    app = get_object_or_404(App, slug=slug, activo=True)
    Busqueda.objects.create(termino=app.nombre, app_encontrada=app, ip_hash=_hash_ip(request))
    relacionadas = App.objects.filter(categoria=app.categoria, activo=True).exclude(id=app.id)[:4]
    return render(request, "detector/detalle.html", {"app": app, "relacionadas": relacionadas})
