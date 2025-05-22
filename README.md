# ENTREGA CONVOCATORIA MAYO

# ENTREGA DE PRÁCTICA

## Datos

* Nombre: Adrián Muñoz
* Titulación: Ingeniería en Tecnologías de la Telecomunicación
* Cuenta en laboratorios: adrimm
* Cuenta URJC: a.munozm.2021@alumnos.urjc.es
* Video básico (url): https://www.youtube.com/watch?v=6OCmZZMRA8s
* Video parte opcional (url): https://www.youtube.com/watch?v=VhpBB2SarOY
* Despliegue (url): https://adrimm.pythonanywhere.com/
* Contraseñas: juan/arjona1234 maria/ismav1234 guille/llermo4567
* Cuenta Admin Site: adrimm/adrimm

## Resumen parte obligatoria
La aplicación GameRank es una plataforma interactiva y moderna diseñada para explorar, valorar y comentar videojuegos con una experiencia intuitiva y atractiva. Entre sus principales características destacan:

- Un listado principal interactivo de juegos ordenado automáticamente por puntuación media, permitiendo descubrir fácilmente los juegos mejor valorados.

- Página detallada por juego con imagen destacada, descripción completa, información técnica, sistema intuitivo de valoración y comentarios organizados por fecha.

- Innovadora versión dinámica (con HTMX) que actualiza comentarios en tiempo real, formularios dinámicos y publicación instantánea sin recargar la página, mejorando significativamente la experiencia del usuario.

- Potente sistema de autenticación y configuración personalizable que permite a cada usuario votar, comentar y seguir juegos de forma individual, con guardado automático de sus preferencias.

- Completa área personal del usuario con resúmenes estadísticos claros y precisos sobre sus valoraciones, comentarios y juegos seguidos, facilitando un seguimiento eficaz de la actividad en la plataforma.

- Interfaz visualmente agradable y adaptable gracias al uso de Bootstrap, con opciones personalizables de fuente y tamaño de texto.

- Integración del Admin Site para gestión avanzada de usuarios y contenido.

- Métricas actualizadas en tiempo real en el pie de página que ofrecen información valiosa sobre la participación general y personal.

- Recursos JSON individuales por juego para una fácil integración y consulta externa.

- Página de ayuda clara y accesible, mejorando la comprensión y el uso de la aplicación.## Lista partes opcionales

## Lista partes opcionales
* Sistema de "Me gusta / No me gusta" en comentarios:
  - Innovador sistema interactivo basado en HTMX que permite a los usuarios valorar comentarios con votos positivos o negativos sin necesidad de recargar la página. Esta funcionalidad no solo cumple con lo solicitado, sino que aporta una experiencia de usuario mucho más dinámica y agradable gracias a la actualización visual inmediata de cada comentario.
* Favicon personalizado:
  - Se ha añadido un favicon específico y personalizado que proporciona identidad visual consistente a la aplicación en todas las pestañas del navegador, mejorando la experiencia visual del usuario.
* Integración avanzada con APIs públicas (FreeToGame + MMOBomb):
  - Se ha implementado una funcionalidad optativa que unifica los datos de dos APIs externas (FreeToGame y MMOBomb) en una única vista de exploración.
  - Los juegos se fusionan automáticamente evitando duplicados mediante comparación de títulos, lo que garantiza que cada juego aparezca una sola vez, incluso si figura en ambas fuentes.
  - Se permite al usuario filtrar los juegos por plataforma (PC y Browser).
  - Además, la implementación está adaptada al entorno de despliegue:
    - En desarrollo local (`DEBUG=True`), los datos se descargan en tiempo real desde las APIs para asegurar información actualizada.
    - En producción (`DEBUG=False`, como en PythonAnywhere), se utilizan copias locales predescargadas en formato JSON debido a las restricciones de acceso a URLs externas impuestas por la plataforma.
* Internacionalización de la interfaz:
  - Se ha configurado el sistema de traducción automática según el idioma del navegador, con todos los textos de la interfaz marcados y traducidos al inglés usando makemessages y compilemessages.
* Tests avanzados y robustos:
  - Completa suite de pruebas automatizadas incluyendo tests unitarios detallados para métodos críticos de los modelos (puntuacion_media, num_likes, etc.), pruebas específicas para funciones auxiliares clave (comentarios_con_votos), y condiciones límite (como evitar comentarios vacíos). Estas pruebas garantizan la robustez, fiabilidad y calidad técnica de la aplicación, facilitando la detección temprana y eficaz de posibles errores.