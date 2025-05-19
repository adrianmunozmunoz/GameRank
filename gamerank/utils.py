from django.shortcuts import redirect
from .models import Seguimiento, Comentario

def procesar_seguimiento(request, juegos, redirigir_a):
    """
    Procesa las acciones de seguir o dejar de seguir juegos para un usuario.
    Retorna un redirect si se ha pulsado algún botón, o None si no se ha hecho nada.
    """
    if request.method == 'POST':
        for juego in juegos:
            if f"Seguir_{juego.id_juego}" in request.POST:
                Seguimiento.objects.get_or_create(usuario=request.user, juego=juego)
                return redirect(redirigir_a)
            elif f"Dejar_seguir_{juego.id_juego}" in request.POST:
                Seguimiento.objects.filter(usuario=request.user, juego=juego).delete()
                return redirect(redirigir_a)
    return None


def obtener_juegos_seguidos_ids(usuario):
    """
    Devuelve un conjunto de ID de juegos que el usuario sigue actualmente.
    """
    return set(
        Seguimiento.objects.filter(usuario=usuario).values_list('juego_id', flat=True)
    )

def comentarios_con_votos(juego):
    """
    Devuelve una lista de comentarios del juego, con num_likes y num_dislikes preprocesados.
    """
    comentarios = Comentario.objects.filter(juego=juego)
    for c in comentarios:
        c.num_likes = c.num_likes()
        c.num_dislikes = c.num_dislikes()
    return comentarios