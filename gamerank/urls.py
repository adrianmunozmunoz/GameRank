from django.urls import path
from django.views.generic import TemplateView

from . import views

urlpatterns = [

    # PÁGINA PRINCIPAL Y JUEGO
    path('', views.inicio, name='inicio'),
    path('juego/<str:id_juego>/', views.detalle_juego, name='detalle_juego'),

    # USUARIO
    path('usuario/', views.pagina_usuario, name='pagina_usuario'),
    path('votados/', views.juegos_votados, name='juegos_votados'),
    path('seguidos/', views.juegos_seguidos, name='juegos_seguidos'),
    path('configuracion/', views.configuracion, name='configuracion'),
    path('ayuda/', TemplateView.as_view(template_name='gamerank/ayuda.html'), name='ayuda'),

    # COMENTARIOS
    path("comentario/<int:id_comentario>/votar/", views.votar_comentario, name="votar_comentario"),
    path("comentario/<int:id_comentario>/votar_htmx/", views.votar_comentario_htmx, name="votar_comentario_htmx"),

    # JSON
    path("juego/<str:id_juego>.json", views.juego_json, name="juego_json"),

    # HTMX
    path("juego/<str:id_juego>/htmx/", views.detalle_juego_htmx, name="detalle_juego_htmx"),
    path("juego/<str:id_juego>/htmx/comentarios/", views.comentarios_htmx, name="comentarios_htmx"),
    path("juego/<str:id_juego>/htmx/comentario/", views.publicar_comentario_htmx, name="publicar_comentario_htmx"),

    # EXTRAS
    path("juegos/api/", views.juegos_api_unificados, name="juegos_api"),]