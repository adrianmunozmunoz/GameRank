from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from gamerank.models import Juego, Comentario, Valoracion
from datetime import date
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

