from .models import Juego, Comentario, Valoracion, ConfiguracionUsuario

def user_alias(request):
    """
    Devuelve el alias del usuario autenticado, o 'Anónimo' si no ha iniciado sesión.
    """
    if request.user.is_authenticated:
        try:
            return {'user_alias': request.user.configuracionusuario.alias or request.user.username}
        except ConfiguracionUsuario.DoesNotExist:
            return {'user_alias': request.user.username}
    return {'user_alias': "Anónimo"}


def metricas_footer(request):
    """
    Devuelve Juegos/comentarios totales + votos/comentarios del usuario
    """
    context = {
        'total_juegos': Juego.objects.count(),
        'total_comentarios': Comentario.objects.count(),
    }

    if request.user.is_authenticated:
        context.update({
            'votos_usuario': Valoracion.objects.filter(usuario=request.user).count(),
            'comentarios_usuario': Comentario.objects.filter(usuario=request.user).count(),
        })

    return context

def configuracion_usuario(request):
    """
    Sirve para cargar el estilo visual personalizado del usuario en todas las plantillas.
    Evita tener que pasar esa info manualmente desde cada vista.
    """
    if request.user.is_authenticated:
        try:
            config = ConfiguracionUsuario.objects.get(usuario=request.user)
        except ConfiguracionUsuario.DoesNotExist:
            config = None
        return {'config': config}
    return {'config': None}