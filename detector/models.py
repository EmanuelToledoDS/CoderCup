from django.db import models
from django.utils import timezone


class FactorRiesgo(models.Model):
    """
    Catálogo de factores de riesgo que puede tener una app/plataforma.
    Se cargan una sola vez y se reutilizan (relación M2M) en cada App.
    """

    class Categoria(models.TextChoices):
        CONTACTO = "contacto", "Contacto con desconocidos"
        CONTENIDO = "contenido", "Contenido inapropiado"
        PRIVACIDAD = "privacidad", "Privacidad y datos"
        ECONOMICO = "economico", "Riesgo económico"
        PSICOSOCIAL = "psicosocial", "Impacto psicosocial"

    nombre = models.CharField(max_length=120, unique=True)
    descripcion = models.CharField(max_length=280)
    categoria = models.CharField(max_length=20, choices=Categoria.choices)
    icono = models.CharField(
        max_length=40,
        default="alert-triangle",
        help_text="Nombre de icono (lucide) para mostrar en la UI.",
    )

    class Meta:
        verbose_name = "Factor de riesgo"
        verbose_name_plural = "Factores de riesgo"
        ordering = ["categoria", "nombre"]

    def __str__(self):
        return self.nombre


class App(models.Model):
    """
    Registro curado manualmente de una app/plataforma con su rating de edad.
    Este es el núcleo de la base de datos "verificada" (no generada por IA).
    """

    class NivelRiesgo(models.TextChoices):
        BAJO = "bajo", "Bajo"
        MEDIO = "medio", "Medio"
        ALTO = "alto", "Alto"
        MUY_ALTO = "muy_alto", "Muy alto"

    class Fuente(models.TextChoices):
        CURADA = "curada", "Base de datos curada"
        IA = "ia", "Estimación por IA"

    nombre = models.CharField(max_length=120, db_index=True)
    slug = models.SlugField(max_length=140, unique=True)
    categoria = models.CharField(max_length=80, blank=True)
    descripcion_corta = models.CharField(max_length=280)
    edad_recomendada = models.PositiveSmallIntegerField(
        help_text="Edad mínima recomendada, en años (0-18)."
    )
    nivel_riesgo = models.CharField(max_length=10, choices=NivelRiesgo.choices)
    justificacion = models.TextField(
        help_text="Explicación breve de por qué se asignó esta edad/riesgo."
    )
    fuente = models.CharField(
        max_length=10, choices=Fuente.choices, default=Fuente.CURADA
    )
    fuente_detalle = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ej: Common Sense Media, App Store, PEGI, ESRB.",
    )
    factores = models.ManyToManyField(FactorRiesgo, related_name="apps", blank=True)
    logo_emoji = models.CharField(
        max_length=8,
        blank=True,
        help_text="Emoji simple para mostrar mientras no haya logo real.",
    )
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "App"
        verbose_name_plural = "Apps"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre

    @property
    def color_riesgo(self):
        return {
            self.NivelRiesgo.BAJO: "#4ECDC4",
            self.NivelRiesgo.MEDIO: "#FFB84D",
            self.NivelRiesgo.ALTO: "#FF6B5B",
            self.NivelRiesgo.MUY_ALTO: "#E23B32",
        }.get(self.nivel_riesgo, "#FFB84D")

    @property
    def angulo_dial(self):
        edad = min(max(self.edad_recomendada, 0), 18)
        return round((edad / 18) * 180) - 90

    @property
    def mensaje_riesgo(self):
        return {
            self.NivelRiesgo.BAJO: "Apta, con supervisión habitual",
            self.NivelRiesgo.MEDIO: "Requiere acompañamiento",
            self.NivelRiesgo.ALTO: "No recomendada sin supervisión",
            self.NivelRiesgo.MUY_ALTO: "No recomendada para menores",
        }.get(self.nivel_riesgo, "")


class Busqueda(models.Model):
    """
    Log de búsquedas realizadas por los usuarios. Sirve para mostrar
    'más buscadas' y para saber qué apps pedir que se carguen a futuro.
    """

    termino = models.CharField(max_length=150)
    app_encontrada = models.ForeignKey(
        App, null=True, blank=True, on_delete=models.SET_NULL, related_name="busquedas"
    )
    resuelta_por_ia = models.BooleanField(default=False)
    fecha = models.DateTimeField(default=timezone.now)
    ip_hash = models.CharField(max_length=64, blank=True)

    class Meta:
        verbose_name = "Búsqueda"
        verbose_name_plural = "Búsquedas"
        ordering = ["-fecha"]

    def __str__(self):
        return f"{self.termino} ({self.fecha:%Y-%m-%d %H:%M})"
