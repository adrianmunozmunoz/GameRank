from django.contrib import admin

from gamerank.models import Juego, Comentario, Valoracion, Seguimiento, ConfiguracionUsuario, VotoComentario

# Register your models here.

admin.site.register(Juego)
admin.site.register(Comentario)
admin.site.register(Valoracion)
admin.site.register(Seguimiento)
admin.site.register(ConfiguracionUsuario)
admin.site.register(VotoComentario)
