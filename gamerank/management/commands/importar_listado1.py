import xml.etree.ElementTree as ET

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from gamerank.models import Juego

class Command(BaseCommand):
    help = "Importa juegos desde listado1.xml (prefijo LIS1-)"

    def handle(self, *args, **kwargs):
        ruta = os.path.join(settings.BASE_DIR, "listado1.xml")
        try:
            root = ET.parse(ruta).getroot()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error al leer el archivo XML: {e}"))
            return

        for juego_elem in root.findall('game'):
            id_juego = "LIS1-" + juego_elem.find('id').text.strip()

            juego, creado = Juego.objects.get_or_create(
                id_juego=id_juego,
                defaults={
                    'titulo': juego_elem.findtext('title', '').strip(),
                    'plataforma': juego_elem.findtext('platform', '').strip(),
                    'genero': juego_elem.findtext('genre', '').strip(),
                    'desarrollador': juego_elem.findtext('developer', '').strip(),
                    'publicador': juego_elem.findtext('publisher', '').strip(),
                    'descripcion_corta': juego_elem.findtext('short_description', '').strip(),
                    'imagen_miniatura': juego_elem.findtext('thumbnail', '').strip(),
                    'url_juego': juego_elem.findtext('game_url', '').strip(),
                    'url_perfil': juego_elem.findtext('freetogame_profile_url', '').strip(),
                }
            )

            fecha = juego_elem.findtext('release_date', '').strip()
            if fecha:
                try:
                    juego.fecha_lanzamiento = fecha  # Formato esperado: 'YYYY-MM-DD'
                    juego.save()
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f"Fecha inválida para {id_juego}: {e}"))

            estado = "Creado" if creado else "Ya existía"
            self.stdout.write(f"{estado}: {juego.titulo}")
