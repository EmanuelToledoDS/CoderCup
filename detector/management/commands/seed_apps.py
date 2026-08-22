from django.core.management.base import BaseCommand
from django.utils.text import slugify

from detector.models import App, FactorRiesgo

FACTORES = [
    ("Contacto con desconocidos", "Permite mensajes o contacto directo de personas no conocidas.", "contacto"),
    ("Chat de voz/video abierto", "Comunicación en tiempo real sin moderación consistente.", "contacto"),
    ("Geolocalización", "Puede exponer la ubicación del usuario.", "privacidad"),
    ("Compras in-app", "Permite gastar dinero real dentro de la app.", "economico"),
    ("Contenido no moderado", "Contenido generado por usuarios sin filtro uniforme.", "contenido"),
    ("Contenido para adultos", "Puede exponer contenido sexual, violento o explícito.", "contenido"),
    ("Presión social / estética", "Fomenta comparación social o presión por imagen.", "psicosocial"),
    ("Recolección de datos", "Recolecta datos personales para publicidad.", "privacidad"),
    ("Mensajes efímeros", "Mensajes que desaparecen, dificultan la supervisión.", "privacidad"),
    ("Vínculo parasocial con IA", "Chatbots que simulan relaciones emocionales.", "psicosocial"),
    ("Historial de casos de grooming", "Reportes públicos de abuso o grooming en la plataforma.", "contacto"),
]

APPS = [
    ("YouTube Kids", "Video", "Contenido curado para chicos, sin chat.", 4, "bajo", "Catálogo filtrado especialmente para audiencia infantil, sin mensajería.", "App Store / Play Store", "📺", []),
    ("Duolingo", "Educación", "App de aprendizaje de idiomas.", 8, "bajo", "Sin chat con desconocidos, contenido educativo controlado.", "App Store", "🦉", []),
    ("Minecraft", "Juegos", "Sandbox creativo, multijugador opcional.", 8, "medio", "El modo multijugador online habilita chat de texto con otros jugadores.", "ESRB", "🧱", ["Chat de voz/video abierto", "Contacto con desconocidos"]),
    ("Among Us", "Juegos", "Juego social de deducción online.", 8, "medio", "Incluye chat de texto entre jugadores desconocidos durante las partidas.", "ESRB", "🚀", ["Contacto con desconocidos"]),
    ("Zoom", "Videollamadas", "Videollamadas grupales.", 8, "medio", "El riesgo depende de la supervisión: los links pueden compartirse con terceros.", "Common Sense Media", "🎥", ["Contacto con desconocidos"]),
    ("Roblox Studio", "Creación", "Herramienta de creación de juegos.", 10, "bajo", "El modo de creación en sí no expone chat directo con desconocidos.", "Common Sense Media", "🛠️", []),
    ("Pinterest", "Redes sociales", "Plataforma de descubrimiento visual.", 12, "bajo", "Contenido mayormente seguro, aunque requiere filtrado de búsquedas sensibles.", "Common Sense Media", "📌", ["Contenido no moderado"]),
    ("Spotify", "Música", "Streaming de música y podcasts.", 12, "bajo", "Sin chat; algunas letras y podcasts pueden incluir contenido explícito marcado.", "App Store", "🎧", ["Contenido para adultos"]),
    ("Netflix", "Streaming", "Streaming de series y películas.", 12, "medio", "Contenido para adultos accesible si no se configura el perfil infantil.", "Common Sense Media", "🎬", ["Contenido para adultos"]),
    ("Fortnite", "Juegos", "Battle royale multijugador.", 12, "medio", "Chat de voz con desconocidos y sistema de compras in-app frecuentes.", "ESRB", "🎮", ["Chat de voz/video abierto", "Compras in-app"]),
    ("BeReal", "Redes sociales", "Red social de fotos espontáneas.", 13, "medio", "Comparte ubicación aproximada y fomenta exposición social constante.", "Common Sense Media", "📸", ["Geolocalización", "Presión social / estética"]),
    ("WhatsApp", "Mensajería", "Mensajería instantánea.", 13, "medio", "Los grupos y links permiten contacto de números no guardados en agenda.", "Meta / App Store", "💬", ["Contacto con desconocidos"]),
    ("YouTube", "Video", "Plataforma de video general.", 13, "medio", "El algoritmo puede exponer contenido no apto pese a los filtros disponibles.", "Common Sense Media", "▶️", ["Contenido no moderado", "Recolección de datos"]),
    ("Facebook", "Redes sociales", "Red social general.", 13, "medio", "Grupos públicos y solicitudes de amistad habilitan contacto con desconocidos.", "Common Sense Media", "👥", ["Contacto con desconocidos", "Recolección de datos"]),
    ("Character.AI", "Chat con IA", "Chatbots de personajes con IA.", 13, "medio", "Fomenta vínculos parasociales prolongados con personajes de IA.", "Common Sense Media", "🤖", ["Vínculo parasocial con IA", "Contenido no moderado"]),
    ("VSCO", "Redes sociales", "Red social de edición y fotos.", 13, "medio", "Comentarios abiertos y fuerte foco en estética corporal.", "Common Sense Media", "🌤️", ["Presión social / estética", "Contenido no moderado"]),
    ("Yubo", "Redes sociales", "App de \"hacer amigos\" con livestream.", 13, "muy_alto", "Foco frecuente de alertas de seguridad por contacto entre adultos y menores vía livestream.", "Common Sense Media", "🔴", ["Contacto con desconocidos", "Historial de casos de grooming", "Geolocalización"]),
    ("Roblox", "Juegos", "Plataforma de juegos creados por usuarios.", 13, "alto", "Chat abierto entre jugadores, compras in-app y señalada repetidamente como espacio de riesgo de contacto con depredadores.", "Common Sense Media", "🧊", ["Chat de voz/video abierto", "Contacto con desconocidos", "Compras in-app", "Historial de casos de grooming"]),
    ("Discord", "Mensajería", "Chat de comunidades por voz y texto.", 13, "alto", "Servidores con moderación desigual; algunos incluyen contenido para adultos.", "Common Sense Media", "🎮", ["Chat de voz/video abierto", "Contenido para adultos", "Contacto con desconocidos"]),
    ("Instagram", "Redes sociales", "Red social de fotos y video.", 13, "alto", "Mensajes directos abiertos, fuerte presión social y algoritmo poco filtrado.", "Common Sense Media", "📷", ["Contacto con desconocidos", "Presión social / estética", "Recolección de datos"]),
    ("Snapchat", "Redes sociales", "Mensajería con fotos efímeras.", 13, "alto", "Los mensajes que desaparecen dificultan la supervisión parental; comparte ubicación.", "Common Sense Media", "👻", ["Mensajes efímeros", "Geolocalización", "Contacto con desconocidos"]),
    ("LinkedIn", "Profesional", "Red social profesional.", 16, "medio", "Enfoque profesional con menor contacto directo riesgoso, pero mensajería abierta.", "Common Sense Media", "💼", ["Contacto con desconocidos"]),
    ("Twitter / X", "Redes sociales", "Red social de microblogging.", 16, "alto", "Contenido no moderado uniformemente y mensajes directos abiertos.", "Common Sense Media", "🐦", ["Contenido no moderado", "Contacto con desconocidos"]),
    ("Telegram", "Mensajería", "Mensajería con canales y grupos masivos.", 16, "alto", "Canales públicos sin moderación centralizada, fácil acceso a contenido sensible.", "Common Sense Media", "✈️", ["Contenido no moderado", "Contacto con desconocidos"]),
    ("Reddit", "Redes sociales", "Foros y comunidades temáticas.", 16, "alto", "Comunidades con moderación muy despareja entre foros.", "Common Sense Media", "👽", ["Contenido no moderado", "Contacto con desconocidos"]),
    ("Twitch", "Streaming", "Plataforma de streaming en vivo.", 15, "alto", "Chat en vivo sin moderación consistente durante las transmisiones.", "Common Sense Media", "🟣", ["Chat de voz/video abierto", "Contenido no moderado"]),
    ("TikTok", "Redes sociales", "Red social de video corto.", 15, "alto", "Reportes de padres sobre lenguaje fuerte, contenido sexual y algoritmo agresivo.", "Common Sense Media", "🎵", ["Contenido para adultos", "Recolección de datos", "Presión social / estética"]),
    ("Kik", "Mensajería", "Mensajería anónima.", 17, "muy_alto", "Historial extenso de casos de grooming por su bajo nivel de verificación.", "Common Sense Media", "💬", ["Contacto con desconocidos", "Historial de casos de grooming"]),
    ("Omegle / chat aleatorio", "Chat", "Chat de video con desconocidos al azar.", 18, "muy_alto", "Conecta aleatoriamente con desconocidos sin ningún tipo de verificación.", "Common Sense Media", "🎲", ["Contacto con desconocidos", "Contenido para adultos", "Historial de casos de grooming"]),
    ("Apps de citas (Tinder y similares)", "Citas", "Apps de encuentros para adultos.", 18, "muy_alto", "Diseñadas explícitamente para contacto romántico/sexual entre adultos.", "App Store", "❤️", ["Contacto con desconocidos", "Contenido para adultos"]),
]


class Command(BaseCommand):
    help = "Carga los factores de riesgo y las 30 apps curadas iniciales."

    def handle(self, *args, **options):
        factor_objs = {}
        for nombre, desc, cat in FACTORES:
            obj, _ = FactorRiesgo.objects.update_or_create(
                nombre=nombre, defaults={"descripcion": desc, "categoria": cat}
            )
            factor_objs[nombre] = obj
        self.stdout.write(self.style.SUCCESS(f"{len(factor_objs)} factores de riesgo cargados."))

        creadas = 0
        for nombre, cat, desc_corta, edad, riesgo, justif, fuente_detalle, emoji, factores in APPS:
            app, created = App.objects.update_or_create(
                slug=slugify(nombre),
                defaults=dict(
                    nombre=nombre,
                    categoria=cat,
                    descripcion_corta=desc_corta,
                    edad_recomendada=edad,
                    nivel_riesgo=riesgo,
                    justificacion=justif,
                    fuente=App.Fuente.CURADA,
                    fuente_detalle=fuente_detalle,
                    logo_emoji=emoji,
                    activo=True,
                ),
            )
            app.factores.set([factor_objs[f] for f in factores])
            creadas += 1 if created else 0

        self.stdout.write(self.style.SUCCESS(f"{len(APPS)} apps procesadas ({creadas} nuevas)."))
