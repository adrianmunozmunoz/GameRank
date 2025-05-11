import os
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
import requests

from gamerankproject import settings
from .models import Juego, Comentario, Valoracion, Seguimiento, ConfiguracionUsuario, VotoComentario

def procesar_seguimiento(request, juegos, redireccion):
    """
    Procesa los formularios de seguir/dejar de seguir juegos.
    Si se ha pulsado algún botón, realiza el cambio en la base de datos y redirige.
    No devuelve nada. La vista que lo llama debe encargarse de recalcular los datos tras el POST.
    """
    if request.method == 'POST':
        # Conjunto de IDs de juegos que el usuario ya sigue
        seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))

        for juego in juegos:
            seguir_key = f"Seguir_{juego.id_juego}"
            dejar_seguir_key = f"Dejar_seguir_{juego.id_juego}"

            if seguir_key in request.POST and juego.id_juego not in seguidos_ids:
                Seguimiento.objects.create(usuario=request.user, juego=juego)
                return redirect(redireccion)

            if dejar_seguir_key in request.POST and juego.id_juego in seguidos_ids:
                Seguimiento.objects.filter(usuario=request.user, juego=juego).delete()
                return redirect(redireccion)

def inicio(request):
    """
    Página principal que muestra los juegos ordenados por puntuación media.
    Si se hace POST desde botones seguir/dejar de seguir, se procesa y se redirige.
    Luego se calcula seguidos_ids y se marca cada juego como seguido o no.
    """
    juegos = list(Juego.objects.all())
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)

    if request.user.is_authenticated:
        procesar_seguimiento(request, juegos, 'inicio')
        # Recalcular seguidos tras posibles cambios
        seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))
        for j in juegos:
            j.seguido = j.id_juego in seguidos_ids
    else:
        seguidos_ids = set()

    return render(request, 'gamerank/inicio.html', {
        'juegos': juegos,
        'seguidos_ids': seguidos_ids,
    })

def detalle_juego(request, id_juego):
    """
    Muestra la ficha de un juego con su información detallada, comentarios y formulario
    para votar, comentar y seguir/dejar de seguir. Solo disponible para usuarios autenticados.
    """
    # Buscar el juego por su ID o lanzar error 404 si no existe
    juego = get_object_or_404(Juego, id_juego=id_juego)

    # Obtener todos los comentarios del juego, ordenados del más reciente al más antiguo
    comentarios = Comentario.objects.filter(juego=juego).order_by('-fecha')

    # Por cada cometario obtener el número de likes y dislikes
    for c in comentarios:
        c.num_likes = c.num_likes()
        c.num_dislikes = c.num_dislikes()

    # Inicializamos variables por si el usuario no está autenticado
    valoracion_usuario = None
    seguimiento_usuario = None

    if request.user.is_authenticated:
        # Comprobar si el usuario ya ha votado este juego
        valoracion_usuario = Valoracion.objects.filter(juego=juego, usuario=request.user).first()

        # Comprobar si el usuario está siguiendo este juego
        seguimiento_usuario = Seguimiento.objects.filter(juego=juego, usuario=request.user).first()

        if request.method == "POST":
            # 1. Añadir un comentario
            if "texto_comentario" in request.POST:
                texto = request.POST.get("texto_comentario", "").strip()
                if texto:
                    Comentario.objects.create(
                        juego=juego,
                        usuario=request.user,
                        texto=texto,
                        fecha=timezone.now()
                    )
                    return redirect("detalle_juego", id_juego=id_juego)

            # 2. Votar (solo si no ha votado antes)
            elif "voto" in request.POST and not valoracion_usuario:
                try:
                    valor = int(request.POST.get("voto"))
                    if 0 <= valor <= 5:
                        Valoracion.objects.create(juego=juego, usuario=request.user, voto=valor)
                        return redirect("detalle_juego", id_juego=id_juego)
                except ValueError:
                    pass  # Ignorar votos inválidos

            # 3. Seguir el juego
            elif "seguir" in request.POST and not seguimiento_usuario:
                Seguimiento.objects.create(juego=juego, usuario=request.user)
                return redirect("detalle_juego", id_juego=id_juego)

            # 4. Dejar de seguir el juego
            elif "dejar_seguir" in request.POST and seguimiento_usuario:
                seguimiento_usuario.delete()
                return redirect("detalle_juego", id_juego=id_juego)

    # Renderizar la plantilla con todos los datos necesarios
    return render(request, "gamerank/detalle_juego.html", {
        "juego": juego,
        "comentarios": comentarios,
        "valoracion_usuario": valoracion_usuario,
        "seguimiento_usuario": seguimiento_usuario,
        "rango_votacion": range(1, 6),  # Para el formulario de votación (1–5)
    })

@login_required
def pagina_usuario(request):
    """
    Vista de la página de usuario autenticado.
    Muestra:
      - Número total de juegos y comentarios del sistema.
      - Número de votaciones y comentarios del usuario.
      - Puntuación media del usuario.
      - Juegos votados con sus puntuaciones.
      - Juegos seguidos.
      - Comentarios realizados por el usuario.
    """
    usuario = request.user

    # Valoraciones del usuario
    valoraciones_usuario = Valoracion.objects.filter(usuario=usuario)
    num_votaciones = valoraciones_usuario.count()
    media_usuario = valoraciones_usuario.aggregate(media=Avg('voto'))['media']
    media_usuario = round(media_usuario, 2) if media_usuario is not None else None

    # Comentarios del usuario
    comentarios_usuario = Comentario.objects.filter(usuario=usuario).select_related('juego')
    num_comentarios_usuario = comentarios_usuario.count()

    # Juegos votados con puntuación
    juegos_votados = [(v.juego, v.voto) for v in valoraciones_usuario.select_related('juego')]

    # Juegos seguidos por el usuario
    juegos_seguidos = Juego.objects.filter(seguimiento__usuario=usuario).distinct()

    return render(request, 'gamerank/pagina_usuario.html', {
        'user': usuario,
        'num_votaciones': num_votaciones,
        'media_usuario': media_usuario,
        'num_comentarios_usuario': num_comentarios_usuario,
        'juegos_votados': juegos_votados,
        'juegos_seguidos': juegos_seguidos,
        'comentarios_usuario': comentarios_usuario,
    })

@login_required
def juegos_votados(request):
    """
    Muestra los juegos votados por el usuario, ordenados por su puntuación.
    Permite seguir/dejar de seguir directamente desde esta vista.
    """
    valoraciones = Valoracion.objects.filter(usuario=request.user).select_related('juego')
    juegos = []

    for v in valoraciones:
        juego = v.juego
        juego.mi_voto = v.voto
        juegos.append(juego)

    juegos.sort(key=lambda j: j.mi_voto, reverse=True)

    # Procesar seguimiento y redirigir si es necesario
    procesar_seguimiento(request, juegos, 'juegos_votados')

    # Recalcular juegos seguidos tras el POST
    seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))

    return render(request, 'gamerank/juegos_votados.html', {
        'juegos': juegos,
        'seguidos_ids': seguidos_ids,
    })

@login_required
def juegos_seguidos(request):
    """
    Muestra los juegos que el usuario sigue.
    Se permite dejar de seguir directamente desde esta vista.
    """
    # Obtener los juegos seguidos antes del posible POST
    seguimientos = Seguimiento.objects.filter(usuario=request.user).select_related('juego')
    juegos = [s.juego for s in seguimientos]
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)

    # Procesar cambios y redirigir si corresponde
    procesar_seguimiento(request, juegos, 'juegos_seguidos')

    # Recalcular tras POST para evitar necesidad de doble recarga
    seguimientos = Seguimiento.objects.filter(usuario=request.user).select_related('juego')
    juegos = [s.juego for s in seguimientos]
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)
    seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))

    return render(request, 'gamerank/juegos_seguidos.html', {
        'juegos': juegos,
        'seguidos_ids': seguidos_ids,
    })


@login_required
def configuracion(request):
    """
    Permite al usuario cambiar su alias, tipo de letra y tamaño de texto.
    """
    config, _ = ConfiguracionUsuario.objects.get_or_create(usuario=request.user)

    if request.method == "POST":
        alias = request.POST.get("alias", "").strip()
        tipo_letra = request.POST.get("tipo_letra", "")
        tamano_texto = request.POST.get("tamano_texto", "")

        config.alias = alias
        config.tipo_letra = tipo_letra
        config.tamano_texto = tamano_texto
        config.save()

        return redirect("configuracion")

    return render(request, "gamerank/configuracion.html")

@login_required
def votar_comentario(request, id_comentario):
    """
    Permite a un usuario dar 'me gusta' o 'no me gusta' a un comentario.
    Actualiza el voto si ya había uno anterior.
    """
    comentario = get_object_or_404(Comentario, id=id_comentario)
    tipo = request.POST.get("tipo")

    if tipo in ['like', 'dislike']:
        VotoComentario.objects.update_or_create(
            usuario=request.user,
            comentario=comentario,
            defaults={'tipo': tipo}
        )

    return redirect(request.META.get('HTTP_REFERER', '/'))

@require_GET
def juego_json(request, id_juego):
    """
    Devuelve los datos de un juego en formato JSON, incluyendo número de comentarios.
    """
    juego = get_object_or_404(Juego, id_juego=id_juego)
    comentarios_count = Comentario.objects.filter(juego=juego).count()
    puntuacion_media = juego.puntuacion_media()

    data = {
        "id_juego": juego.id_juego,
        "titulo": juego.titulo,
        "genero": juego.genero,
        "plataforma": juego.plataforma,
        "desarrollador": juego.desarrollador,
        "publicador": juego.publicador,
        "fecha_lanzamiento": juego.fecha_lanzamiento.strftime('%Y-%m-%d') if juego.fecha_lanzamiento else None,
        "descripcion_corta": juego.descripcion_corta,
        "url_juego": juego.url_juego,
        "imagen_miniatura": juego.imagen_miniatura,
        "puntuacion_media": round(puntuacion_media, 2) if puntuacion_media is not None else None,
        "numero_comentarios": comentarios_count
    }

    return JsonResponse(data)

@login_required
def detalle_juego_htmx(request, id_juego):
    """
    Página principal con HTMX. Carga secciones dinámicas (comentarios + formulario).
    """
    juego = get_object_or_404(Juego, id_juego=id_juego)
    seguido = juego.seguimiento_set.filter(usuario=request.user).exists()
    valoracion_usuario = Valoracion.objects.filter(juego=juego, usuario=request.user).first()

    # Cargar los comentarios para el bloque inicial
    comentarios = Comentario.objects.filter(juego=juego).order_by('-fecha')
    for c in comentarios:
        c.num_likes = c.votos.filter(tipo='like').count()
        c.num_dislikes = c.votos.filter(tipo='dislike').count()

    return render(request, "gamerank/detalle_juego_htmx.html", {
        "juego": juego,
        "seguido": seguido,
        "valoracion_usuario": valoracion_usuario,
        "rango_votacion": range(1, 6),
        "comentarios": comentarios,
    })

@require_GET
@login_required
def comentarios_htmx(request, id_juego):
    """
    Devuelve solo los comentarios del juego en HTML para HTMX.
    """
    juego = get_object_or_404(Juego, id_juego=id_juego)
    comentarios = Comentario.objects.filter(juego=juego).order_by('-fecha')
    return render(request, "gamerank/includes/comentarios_htmx.html", {
        "comentarios": comentarios
    })

@require_POST
@login_required
def publicar_comentario_htmx(request, id_juego):
    """
    Publica un nuevo comentario y devuelve la lista HTML actualizada.
    """
    juego = get_object_or_404(Juego, id_juego=id_juego)
    texto = request.POST.get("texto_comentario", "").strip()

    if texto:
        Comentario.objects.create(
            juego=juego,
            usuario=request.user,
            texto=texto,
            fecha=timezone.now()
        )

    comentarios = Comentario.objects.filter(juego=juego).order_by('-fecha')
    return render(request, "gamerank/includes/comentarios_htmx.html", {
        "comentarios": comentarios,
        "juego": juego
    })

@login_required
def votar_comentario_htmx(request, id_comentario):
    """
    Permite votar un comentario de forma dinámica con HTMX.
    Registra 'me gusta' o 'no me gusta' del usuario actual, actualiza contadores
    y devuelve el HTML del comentario actualizado para reemplazarlo en la página.
    """
    comentario = get_object_or_404(Comentario, id=id_comentario)
    tipo = request.POST.get("tipo")

    if tipo in ['like', 'dislike']:
        VotoComentario.objects.update_or_create(
            usuario=request.user,
            comentario=comentario,
            defaults={'tipo': tipo}
        )

    # Cálculo manual de contadores
    comentario.num_likes = comentario.num_likes()
    comentario.num_dislikes = comentario.num_dislikes()

    # Detectar el voto actual del usuario
    comentario.voto_usuario = VotoComentario.objects.filter(usuario=request.user, comentario=comentario).first()

    html = render_to_string("gamerank/includes/comentario_individual.html", {"comentario": comentario, "user": request.user})
    return HttpResponse(html)

def juegos_api_freetogame(request):
    """
    Muestra un formulario para seleccionar plataforma.
    Solo muestra los juegos si se ha enviado un filtro ?plataforma=...
    """
    juegos = []
    plataforma_filtro = request.GET.get("plataforma", "").lower().strip()

    if plataforma_filtro:
        if settings.DEBUG:
            # En local, descarga desde la API
            try:
                response = requests.get("https://www.freetogame.com/api/games", timeout=10)
                response.raise_for_status()
                juegos = response.json()
            except Exception as e:
                print("❌ Error al conectar con la API de FreeToGame:", e)
        else:
            # En producción, carga desde archivo JSON
            try:
                ruta_json = os.path.join(settings.BASE_DIR, "data", "juegos_freetogame_backup.json")
                with open(ruta_json, "r", encoding="utf-8") as f:
                    juegos = json.load(f)
            except Exception as e:
                print("❌ Error al leer el archivo JSON:", e)

        # Aplica el filtro solo si hay datos
        juegos = [j for j in juegos if plataforma_filtro in j.get("platform", "").lower()]

    return render(request, "gamerank/juegos_api.html", {
        "juegos": juegos,
        "plataforma_seleccionada": plataforma_filtro
    })

