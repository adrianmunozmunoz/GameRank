import os
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.db.models import Avg
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_POST
from .utils import procesar_seguimiento, obtener_juegos_seguidos_ids, comentarios_con_votos
from gamerankproject import settings
from .models import Juego, Comentario, Valoracion, Seguimiento, ConfiguracionUsuario, VotoComentario

import requests


def inicio(request):
    """
    Página principal que muestra los juegos ordenados por puntuación media (descendente).
    Si se hace POST desde los botones de seguir/dejar de seguir, se procesa y redirige.
    Si el usuario está autenticado, se marca cuáles sigue actualmente.
    """
    juegos = list(Juego.objects.all())
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)

    seguidos_ids = set()

    if request.user.is_authenticated:
        # Procesar acción de seguimiento si hay POST
        respuesta = procesar_seguimiento(request, juegos, "inicio")
        if respuesta:
            return respuesta

        # Recuperar juegos seguidos para marcar botones activos
        seguidos_ids = obtener_juegos_seguidos_ids(request.user)

        for juego in juegos:
            juego.seguido = juego.id_juego in seguidos_ids

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

    # Carga los comentarios del juego con los contadores de likes y dislikes ya calculados
    comentarios = comentarios_con_votos(juego)

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
            voto = request.POST.get("voto")
            if voto and not valoracion_usuario:
                try:
                    valor = int(voto)
                    if 0 <= valor <= 5:
                        Valoracion.objects.create(juego=juego, usuario=request.user, voto=valor)
                        return redirect("detalle_juego", id_juego=id_juego)
                except ValueError:
                    pass  # Ignorar votos inválidos

            # 3. Seguir el juego
            if "seguir" in request.POST and not seguimiento_usuario:
                Seguimiento.objects.create(juego=juego, usuario=request.user)
                return redirect("detalle_juego", id_juego=id_juego)

            # 4. Dejar de seguir el juego
            if "dejar_seguir" in request.POST and seguimiento_usuario:
                seguimiento_usuario.delete()
                return redirect("detalle_juego", id_juego=id_juego)

    # Renderizar la plantilla con todos los datos necesarios
    return render(request, "gamerank/detalle_juego.html", {
        "juego": juego,
        "comentarios": comentarios,
        "valoracion_usuario": valoracion_usuario,
        "seguimiento_usuario": seguimiento_usuario,
        "rango_votacion": range(1, 6),
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
        juego.puntuacion = juego.puntuacion_media()
        juego.total_votos = juego.total_votos()
        juegos.append(juego)

    juegos.sort(key=lambda j: j.mi_voto, reverse=True)

    # Procesar acción de seguimiento si hay POST
    respuesta = procesar_seguimiento(request, juegos, "inicio")
    if respuesta:
        return respuesta

    # Recuperar juegos seguidos para marcar botones activos
    seguidos_ids = obtener_juegos_seguidos_ids(request.user)

    return render(request, 'gamerank/juegos_votados.html', {
        'juegos': juegos,
        'seguidos_ids': seguidos_ids,
    })

@login_required
def juegos_seguidos(request):
    """
    Muestra los juegos que el usuario sigue, ordenados por puntuación media.
    Permite dejar de seguir juegos directamente desde esta vista.
    """
    seguimientos = Seguimiento.objects.filter(usuario=request.user).select_related('juego')
    juegos = [s.juego for s in seguimientos]
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)

    # Procesar acción de seguimiento si hay POST
    respuesta = procesar_seguimiento(request, juegos, "juegos_seguidos")
    if respuesta:
        return respuesta  # Ojo: nada más debe ir aquí

    # Recuperar juegos seguidos para marcar botones activos
    seguidos_ids = obtener_juegos_seguidos_ids(request.user)

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

        messages.success(request, "Tu configuración se ha actualizado correctamente.")
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

    # Carga los comentarios del juego con los contadores de likes y dislikes ya calculados
    comentarios = comentarios_con_votos(juego)

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
    comentarios = comentarios_con_votos(juego)
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

    comentarios = comentarios_con_votos(juego)
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
    ¿Solo muestra los juegos si se ha enviado un filtro? Plataforma=...
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
            # Para python.anywhere
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