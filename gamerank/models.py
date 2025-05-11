from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.db.models import Avg


class Juego(models.Model):
    """
    Representa un videojuego disponible en la plataforma GameRank.
    Contiene información extraída del XML (y/o APIs externas).
    """
    id_juego = models.CharField(max_length=100, primary_key=True)
    titulo = models.CharField(max_length=100)
    plataforma = models.CharField(max_length=100)
    genero = models.CharField(max_length=100)
    desarrollador = models.CharField(max_length=100, blank=True)
    publicador = models.CharField(max_length=100, blank=True)
    fecha_lanzamiento = models.DateField(null=True, blank=True)
    descripcion_corta = models.TextField(blank=True)
    imagen_miniatura = models.URLField(blank=True)
    url_juego = models.URLField(blank=True)
    url_perfil = models.URLField(blank=True)

    def __str__(self):
        return f"{self.titulo}: {self.id_juego}"

    def puntuacion_media(self):
        """
        Calcula la puntuación media de las valoraciones del juego.
        Devuelve None si no hay votos.
        """
        resultado = self.valoracion_set.aggregate(media=Avg('voto'))
        return round(resultado['media'], 2) if resultado['media'] is not None else None

    def total_votos(self):
        """
        Devuelve el número total de valoraciones recibidas por el juego.
        """
        return self.valoracion_set.count()


class Comentario(models.Model):
    """
    Comentario realizado por un usuario sobre un juego.
    Incluye el texto y la fecha/hora de creación.
    """
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Comentario de {self.usuario.username} en {self.juego.titulo}"

    def num_likes(self):
        return self.votos.filter(tipo='like').count()

    def num_dislikes(self):
        return self.votos.filter(tipo='dislike').count()

class VotoComentario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    comentario = models.ForeignKey('Comentario', on_delete=models.CASCADE, related_name='votos')
    tipo = models.CharField(max_length=10, choices=[('like', 'Me gusta'), ('dislike', 'No me gusta')])

    class Meta:
        unique_together = ('usuario', 'comentario')

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo} a comentario {self.comentario.id}"


class Valoracion(models.Model):
    """
    Valoración (voto de 0 a 5) que un usuario realiza sobre un juego.
    Cada usuario solo puede valorar un juego una vez.
    """
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    voto = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)],
    )

    class Meta:
        unique_together = ('juego', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} → {self.juego.titulo}: {self.voto}"


class Seguimiento(models.Model):
    """
    Asociación entre un usuario y un juego que ha decidido seguir.
    Cada juego solo puede ser seguido una vez por usuario.
    """
    juego = models.ForeignKey(Juego, on_delete=models.CASCADE)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('juego', 'usuario')

    def __str__(self):
        return f"{self.usuario.username} sigue {self.juego.titulo}"


class ConfiguracionUsuario(models.Model):
    """
    Configuración visual personalizada de cada usuario.
    Incluye alias, tipo de letra y tamaño del texto.
    """
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    alias = models.CharField(max_length=100, blank=True)
    tipo_letra = models.CharField(
        max_length=30,
        choices=[
            ('fuente-sans-serif', 'Sans Serif (Rubik)'),
            ('fuente-serif', 'Serif (Roboto Slab)'),
            ('fuente-monospace', 'Monoespaciada (Fira Code)'),
            ('fuente-decorativa', 'Decorativa (Pacifico)'),
        ],
        default='fuente-sans-serif'
    )

    tamano_texto = models.CharField(
        max_length=20,
        choices=[
            ('tamano-small', 'Pequeño'),
            ('tamano-medium', 'Mediano'),
            ('tamano-large', 'Grande'),
            ('tamano-xl', 'Extra grande'),
        ],
        default='tamano-medium'
    )

    def __str__(self):
        return f"Configuración de {self.usuario.username}"