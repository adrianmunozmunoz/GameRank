from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.utils import timezone
from gamerank.models import Juego, Comentario, Valoracion, VotoComentario
from datetime import date
from gamerank.utils import comentarios_con_votos

# Create your tests here.

class GameRankViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')

        self.juego = Juego.objects.create(
            id_juego="LIS1-001",
            titulo="Juego de prueba",
            genero="Accion",
            plataforma="PC",
            desarrollador="DevTest",
            publicador="PubTest",
            fecha_lanzamiento=date(2022, 1, 1),
            descripcion_corta="Prueba de descripcion",
            url_juego="https://example.com",
            imagen_miniatura="https://example.com/img.jpg"
        )

    def test_inicio_view(self):
        response = self.client.get(reverse('inicio'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Juego de prueba")

    def test_detalle_juego_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('detalle_juego', args=[self.juego.id_juego]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.juego.titulo)

    def test_detalle_juego_htmx_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('detalle_juego_htmx', args=[self.juego.id_juego]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.juego.titulo)

    def test_json_recurso_view(self):
        response = self.client.get(reverse('juego_json', args=[self.juego.id_juego]))
        self.assertEqual(response.status_code, 200)
        self.assertIn('application/json', response['Content-Type'])

    def test_usuario_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('pagina_usuario'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.user.username)

    def test_juegos_votados_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('juegos_votados'))
        self.assertEqual(response.status_code, 200)

    def test_juegos_seguidos_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('juegos_seguidos'))
        self.assertEqual(response.status_code, 200)

    def test_configuracion_view(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('configuracion'))
        self.assertEqual(response.status_code, 200)

    def test_ayuda_view(self):
        response = self.client.get(reverse('ayuda'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "GameRank")

class ModeloJuegoTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="test", password="1234")
        self.juego = Juego.objects.create(id_juego="LIS1-test", titulo="Test Game", plataforma="PC", genero="Acción")

    def test_puntuacion_media_sin_votos(self):
        self.assertIsNone(self.juego.puntuacion_media())

    def test_puntuacion_media_con_votos(self):
        Valoracion.objects.create(juego=self.juego, usuario=self.usuario, voto=4)
        self.assertEqual(self.juego.puntuacion_media(), 4)

    def test_total_votos(self):
        Valoracion.objects.create(juego=self.juego, usuario=self.usuario, voto=4)
        self.assertEqual(self.juego.total_votos(), 1)

class ComentarioTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="test", password="1234")
        self.juego = Juego.objects.create(id_juego="LIS1-test", titulo="Juego", plataforma="PC", genero="Puzzle")
        self.comentario = Comentario.objects.create(juego=self.juego, usuario=self.usuario, texto="Bueno", fecha=timezone.now())

    def test_num_likes_y_dislikes(self):
        VotoComentario.objects.create(usuario=self.usuario, comentario=self.comentario, tipo='like')
        self.assertEqual(self.comentario.num_likes(), 1)
        self.assertEqual(self.comentario.num_dislikes(), 0)

class ComentariosConVotosTests(TestCase):
    def setUp(self):
        self.usuario = User.objects.create_user(username="votador", password="1234")
        self.juego = Juego.objects.create(id_juego="LIS1-456", titulo="Votado", plataforma="PC", genero="RPG")
        self.comentario = Comentario.objects.create(juego=self.juego, usuario=self.usuario, texto="Comentario", fecha=timezone.now())
        VotoComentario.objects.create(usuario=self.usuario, comentario=self.comentario, tipo='dislike')

    def test_comentarios_con_votos_devuelve_votos(self):
        comentarios = comentarios_con_votos(self.juego)
        self.assertEqual(len(comentarios), 1)
        self.assertEqual(comentarios[0].num_dislikes, 1)
from django.urls import reverse

class PublicarComentarioHTMXTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="user", password="1234")
        self.juego = Juego.objects.create(id_juego="LIS1-error", titulo="ErrorGame", plataforma="PC", genero="Estrategia")

    def test_no_se_crea_comentario_vacio(self):
        self.client.login(username="user", password="1234")
        url = reverse("publicar_comentario_htmx", args=[self.juego.id_juego])
        response = self.client.post(url, {"texto_comentario": ""})
        self.assertEqual(Comentario.objects.count(), 0)