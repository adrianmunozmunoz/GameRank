import requests
import json
import os

# Construye la ruta absoluta al archivo de destino en /data
ruta_salida = os.path.join(os.path.dirname(__file__), "..", "data", "juegos_freetogame_backup.json")
ruta_salida = os.path.abspath(ruta_salida)

# URL de la API FreeToGame
url = "https://www.freetogame.com/api/games"

try:
    respuesta = requests.get(url, timeout=10)
    respuesta.raise_for_status()
    juegos = respuesta.json()

    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(juegos, f, indent=2, ensure_ascii=False)

    print(f"✅ Datos guardados correctamente en: {ruta_salida}")

except requests.RequestException as e:
    print("❌ Error al conectar con la API de FreeToGame:", e)
