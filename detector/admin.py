from django.contrib import admin
from .models import App, FactorRiesgo, Busqueda


@admin.register(FactorRiesgo)
class FactorRiesgoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "categoria")
    list_filter = ("categoria",)
    search_fields = ("nombre", "descripcion")


@admin.register(App)
class AppAdmin(admin.ModelAdmin):
    list_display = (
        "nombre",
        "edad_recomendada",
        "nivel_riesgo",
        "fuente",
        "activo",
        "actualizado",
    )
    list_filter = ("nivel_riesgo", "fuente", "activo", "categoria")
    search_fields = ("nombre", "descripcion_corta")
    prepopulated_fields = {"slug": ("nombre",)}
    filter_horizontal = ("factores",)


@admin.register(Busqueda)
class BusquedaAdmin(admin.ModelAdmin):
    list_display = ("termino", "app_encontrada", "resuelta_por_ia", "fecha")
    list_filter = ("resuelta_por_ia",)
    search_fields = ("termino",)
    readonly_fields = ("fecha",)
