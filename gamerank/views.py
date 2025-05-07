from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import Avg

from . import models
from .models import Juego, Comentario, Valoracion, Seguimiento, ConfiguracionUsuario


def inicio(request):
    """
    Página principal que muestra los juegos ordenados por puntuación media descendente.
    Permite seguir y dejar de seguir juegos si el usuario está autenticado.
    """
    juegos = list(Juego.objects.all())  # Convertimos el queryset en lista para ordenarlo manualmente
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)  # Ordenamos por puntuación media

    alias = None
    if request.user.is_authenticated:
        # Si el usuario está autenticado, recogemos su alias y los juegos que ya sigue
        alias = request.user.username
        seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))

        if request.method == 'POST':
            # Procesamos la solicitud POST para seguir o dejar de seguir juegos
            for juego in juegos:
                seguir_key = f"Seguir_{juego.id_juego}"
                dejar_seguir_key = f"Dejar_seguir_{juego.id_juego}"

                if seguir_key in request.POST and juego.id_juego not in seguidos_ids:
                    # Crear el seguimiento si aún no se sigue
                    Seguimiento.objects.create(usuario=request.user, juego=juego)
                    return redirect('inicio')

                if dejar_seguir_key in request.POST and juego.id_juego in seguidos_ids:
                    # Eliminar el seguimiento si ya se sigue
                    Seguimiento.objects.filter(usuario=request.user, juego=juego).delete()
                    return redirect('inicio')

        # Añadimos atributo booleano a cada juego para que la plantilla sepa si está seguido
        for j in juegos:
            j.seguido = j.id_juego in seguidos_ids

    return render(request, 'gamerank/index.html', {'juegos': juegos, 'alias': alias})

def detalle_juego(request, id_juego):
    """
    Muestra la ficha de un juego con su información detallada, comentarios y formulario
    para votar, comentar y seguir/dejar de seguir. Solo disponible para usuarios autenticados.
    """
    # Buscar el juego por su ID o lanzar error 404 si no existe
    juego = get_object_or_404(Juego, id_juego=id_juego)

    # Obtener todos los comentarios del juego, ordenados del más reciente al más antiguo
    comentarios = Comentario.objects.filter(juego=juego).order_by('-fecha')

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
    return render(request, "gamerank/game_detail.html", {
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

    # Estadísticas globales
    total_juegos = Juego.objects.count()
    total_comentarios = Comentario.objects.count()

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
        'total_juegos': total_juegos,
        'total_comentarios': total_comentarios,
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
    Muestra los juegos que el usuario ha votado, ordenados por puntuación dada.
    """
    valoraciones = Valoracion.objects.filter(usuario=request.user).select_related('juego')
    juegos = []

    for v in valoraciones:
        juego = v.juego
        juego.mi_voto = v.voto
        juegos.append(juego)

    # Ordenamos por voto descendente
    juegos.sort(key=lambda j: j.mi_voto, reverse=True)

    seguidos_ids = set(Seguimiento.objects.filter(usuario=request.user).values_list('juego_id', flat=True))

    return render(request, 'gamerank/juegos_votados.html', {
        'juegos': juegos,
        'seguidos_ids': seguidos_ids,
    })

@login_required
def juegos_seguidos(request):
    """
    Muestra los juegos que el usuario sigue, ordenados por puntuación media descendente.
    """
    seguimientos = Seguimiento.objects.filter(usuario=request.user).select_related('juego')
    juegos = [s.juego for s in seguimientos]
    juegos.sort(key=lambda j: j.puntuacion_media() or 0, reverse=True)

    return render(request, 'gamerank/juegos_seguidos.html', {
        'juegos': juegos,
        'seguidos_ids': set(j.id_juego for j in juegos),
    })

@login_required
def configuracion(request):
    """
    Permite al usuario cambiar su alias, tipo de letra y tamaño de texto.
    """
    config, _ = ConfiguracionUsuario.objects.get_or_create(usuario=request.user)

    if request.method == "POST":
        alias = request.POST.get("alias", "").strip()
        tipo_letra = request.POST.get("tipo_letra", "sans-serif")
        tamano_texto = request.POST.get("tamano_texto", "medium")

        config.alias = alias
        config.tipo_letra = tipo_letra
        config.tamano_texto = tamano_texto
        config.save()

        return redirect("configuracion")

    return render(request, "gamerank/configuracion.html", {
        "config": config
    })
