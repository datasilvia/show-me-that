import requests
import os

# 🔑 Reemplaza con tu Access Key de Unsplash
ACCESS_KEY = "0byE1o41WexZQJRM5Gy0N2NQIw36GLyZY6XcrUyf_M8"

# 📌 Carpeta donde guardar las imágenes
output_folder = "./imagenes_unsplash_pencil"
os.makedirs(output_folder, exist_ok=True)

# 🔎 Palabra clave para buscar imágenes
query = "pencil"  # Cambia esto por lo que necesites

# 📌 Número total de imágenes deseadas
total_images = 100  
per_page = 30  # Máximo 30 imágenes por solicitud
num_pages = (total_images // per_page) + 1  # Número de páginas necesarias

# 📥 Descargar imágenes de varias páginas
img_count = 0
for page in range(1, num_pages + 1):  # Hacer solicitudes desde page=1 hasta page=num_pages
    print(f"🔍 Descargando página {page}...")

    # URL de la API con paginación
    url = f"https://api.unsplash.com/search/photos?query={query}&per_page={per_page}&page={page}&client_id={ACCESS_KEY}"

    # Hacer la solicitud a la API
    response = requests.get(url)

    # Intentar convertir la respuesta a JSON
    try:
        data = response.json()
    except Exception as e:
        print("❌ Error al convertir la respuesta a JSON:", e)
        print("📌 Respuesta de la API:", response.text)
        exit()

    # Verificar si "results" está en la respuesta
    if "results" not in data:
        print("❌ ERROR: La API no devolvió 'results'. Esto es lo que devolvió:")
        print(data)  # Mostrar la respuesta completa para ver qué está pasando
        exit()

    # Si todo está bien, continuar con la descarga
    for img in data["results"]:
        if img_count >= total_images:
            break  # Detener si ya descargamos suficientes imágenes

        img_url = img["urls"]["full"]  # URL de la imagen en alta calidad
        img_response = requests.get(img_url)

        # Guardar la imagen
        img_path = os.path.join(output_folder, f"{query}_{img_count}.jpg")
        with open(img_path, "wb") as file:
            file.write(img_response.content)

        print(f"✅ Imagen descargada: {img_path}")
        img_count += 1

print("🎉 Descarga completada.")
