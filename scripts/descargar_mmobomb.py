import requests
import json
import os

# Ruta de guardado
output_path = os.path.join("data", "juegos_mmobomb_backup.json")

# URL de la API MMOBomb
url = "https://www.mmobomb.com/api1/games"

try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    juegos = response.json()

    # Guardar en archivo
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(juegos, f, ensure_ascii=False, indent=2)

    print(f"✅ Se han guardado {len(juegos)} juegos en {output_path}")

except Exception as e:
    print("❌ Error al descargar los juegos de MMOBomb:", e)
