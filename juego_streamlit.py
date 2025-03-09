import streamlit as st
import cv2
import torch
import requests
import html
import numpy as np
import pandas as pd
import time
import tensorflow as tf
from PIL import Image
import random
from PIL import Image


# Configuración de la página
st.set_page_config(page_title='Escape Room Trivia', page_icon='🧩', layout='centered')


# Inicialización del estado de sesión
if 'fase' not in st.session_state or st.session_state.fase not in ['inicio', 'trivia']:
    st.session_state.fase = 'inicio'

if 'imagen_capturada' not in st.session_state:
    st.session_state.imagen_capturada = None

if 'objeto_detectado' not in st.session_state:
    st.session_state.objeto_detectado = None

if 'habitacion' not in st.session_state:
    st.session_state.habitacion = 'inicio'


# Inicializar la trivia correctamente para evitar estados inconsistentes
if 'trivia_preguntas' not in st.session_state or st.session_state.fase == 'inicio':
    st.session_state.trivia_preguntas = []
    st.session_state.trivia_index = 0
    st.session_state.trivia_puntuacion = 0
    st.session_state.trivia_estado_respuesta = None



# Cargar modelos de detección
@st.cache_resource  
def cargar_modelos():
    model_yolo = torch.hub.load('./yolov5', 'custom', path='yolov5/yolov5s.pt', source='local')
    model_custom = torch.hub.load('./yolov5', 'custom', path='yolov5/best.pt', source='local')
    return model_yolo, model_custom

model_yolo, model_custom = cargar_modelos()

@st.cache_resource
def cargar_modelo_keras():
    return tf.keras.models.load_model('modelo_keras.h5')

modelo_keras = cargar_modelo_keras()



# Obtener preguntas de trivia
def get_trivia_questions(amount=3, category=9):
    url = f"https://opentdb.com/api.php?amount={amount}&category={category}&type=multiple"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['results']
    return []



categorias_por_habitacion = {
    'Hall': [9, 26, 15, 16],  # Cultura General con Videojuegos, Famosos y Juegos de Mesa
    'kitchen': [17, 18, 19, 30],  # Ciencia
    'bedroom': [11, 12, 14, 31, 32, 13],  # Audiovisual
    'living room': [20, 23, 24, 28, 22],  # Historia
    'outside': [21],  # Deportes
    'library': [10, 25, 29],  # Arte y Literatura
    'pet_friendly': [27],  # Animales
    'spacecraft': [9, 10, 11, 12,13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]  # Final del juego
}



def iniciar_trivia():
    """Inicia la trivia o muestra la imagen final después de responder preguntas en Spacecraft."""

    habitacion_actual = st.session_state.habitacion

    # Si estamos en Spacecraft, verificar si ya terminó la trivia
    if habitacion_actual == 'spacecraft':
        if 'trivia_completada' not in st.session_state:
            st.session_state.trivia_completada = False  # Inicializar variable si no existe

        if not st.session_state.trivia_completada:
            # Si la trivia aún no ha comenzado, iniciar preguntas
            if st.session_state.fase != 'trivia':
                categorias_disponibles = categorias_por_habitacion.get(habitacion_actual, [9])
                categoria_seleccionada = random.choice(categorias_disponibles)
                st.session_state.trivia_preguntas = get_trivia_questions(3, categoria_seleccionada)
                st.session_state.trivia_index = 0
                st.session_state.trivia_puntuacion = 0
                st.session_state.fase = 'trivia'
                st.experimental_rerun()  # Recargar solo una vez
        else:
            # Si la trivia ya se completó, pasar a fase final sin entrar en bucle
            if st.session_state.fase != 'final':  # Evita recargar en bucle
                st.session_state.fase = 'final'
                st.experimental_rerun()
            return

    # Si no es Spacecraft, iniciar la trivia normalmente
    categorias_disponibles = categorias_por_habitacion.get(habitacion_actual, [9])
    categoria_seleccionada = random.choice(categorias_disponibles)

    st.session_state.trivia_preguntas = get_trivia_questions(3, categoria_seleccionada)
    st.session_state.trivia_index = 0
    st.session_state.trivia_puntuacion = 0
    st.session_state.fase = 'trivia'
    st.experimental_rerun()  #  Recargar solo una vez



#  Si estamos en Spacecraft y la trivia ha terminado, mostrar botón para avanzar a la imagen final
if (
    'trivia_index' in st.session_state and
    'trivia_preguntas' in st.session_state and
    st.session_state.habitacion == 'spacecraft' and 
    st.session_state.trivia_index >= len(st.session_state.trivia_preguntas)
):
    st.success("🎉 Has completado la trivia final en Spacecraft.")
    
    if st.button("🚀 Continuar a la escena final"):
        st.session_state.fase = 'final'  # Guardamos la fase en la sesión
        st.query_params["fase"] = "final"  # Ahora guardamos `fase` sin el método antiguo
        st.rerun()  # Recargar para mostrar la imagen final



# Comprobamos si estamos en la fase final desde `st.session_state` o desde los Query Params
fase_actual = st.query_params.get("fase", st.session_state.get("fase", "inicio"))

if fase_actual == 'final':
    st.title("🚀 ¡Has completado el Escape Room! 🌌")
    st.markdown("🎉 Felicidades, has superado todos los desafíos y ahora estás en la nave espacial.")

    # Mostrar la imagen final del juego
    imagen_final = "spacecraft.jpg"  # Asegúrate de que la imagen esté en la carpeta del proyecto
    st.image(imagen_final, caption="Bienvenido a la nave espacial", use_column_width=True)

    st.markdown("🌟 Gracias por jugar. ¿Listo para una nueva aventura?")
    
    st.stop()  # Detener la ejecución para evitar que aparezcan más elementos



# Función para detectar objetos con la cámara
def detectar_objeto(objeto):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error('No se pudo acceder a la cámara.')
        st.stop()

    stframe = st.empty()
    frame_count = 0  
    max_frames = 5  
    last_detected_frame = None

    while frame_count < max_frames:
        ret, frame = cap.read()
        if not ret or frame is None:
            st.error('No se pudo obtener el frame de la cámara.')
            cap.release()
            cv2.destroyAllWindows()
            st.stop()

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  
        results_yolo = model_yolo([frame_rgb])
        results_custom = model_custom([frame_rgb])

        detecciones_yolo = results_yolo.pandas().xyxy[0]
        detecciones_custom = results_custom.pandas().xyxy[0]

        detecciones_yolo = detecciones_yolo[detecciones_yolo['name'] == objeto]
        detecciones_custom = detecciones_custom[detecciones_custom['name'] == objeto]

        detecciones = pd.concat([detecciones_yolo, detecciones_custom])

        for _, row in detecciones.iterrows():
            x1, y1, x2, y2 = int(row['xmin']), int(row['ymin']), int(row['xmax']), int(row['ymax'])
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        stframe.image(frame, channels='BGR', width=400)

        if not detecciones.empty:
            frame_count += 1
            last_detected_frame = frame.copy()
        else:
            frame_count = 0  

    cap.release()
    cv2.destroyAllWindows()



    if last_detected_frame is not None:
        st.session_state.imagen_capturada = last_detected_frame
        st.success(f'¡Has detectado {objeto} con éxito!')
        time.sleep(2)
        iniciar_trivia()  # ← Llamar a la función centralizada para iniciar la trivia

# Presentación del juego
st.title('🔐 Escape Room Trivia')
st.markdown("## ¡Bienvenido al Escape Room Virtual!")
st.markdown("Explora habitaciones, resuelve acertijos y avanza en la aventura.")


# Definición de habitaciones y sus descripciones
habitaciones = {
    'Hall': "Hall - El punto de entrada a la aventura",
    'kitchen': "Kitchen - ¿Qué hay en la cocina?",
    'bedroom': "Bedroom - Un lugar para descansar",
    'living room': "Living Room - ¿Qué encontrarás aquí?",
    'outside': "Outside - Explora el exterior",
    'library': "Library - Donde se guarda el conocimiento",
    'pet_friendly': "Pet Friendly - Un lugar para nuestros amigos peludos",
    'spacecraft': "Spacecraft - El último desafío"
}

# Mostrar el desplegable con todas las habitaciones
st.session_state.habitacion = st.selectbox(
    "Elige una habitación:", 
    list(habitaciones.keys()), 
    format_func=lambda x: habitaciones[x]
)

# Mostrar descripción de la habitación elegida
st.markdown(f"### {habitaciones[st.session_state.habitacion]}")


objetos_por_habitacion = {
    'Hall': 'bottle', 
    'kitchen': 'banana', 
    'bedroom': 'headphones', 
    'living room': 'airplane', 
    'outside': 'basketball', 
    'library': 'book', 
    'pet_friendly': 'cat'  # Solo un objeto permitido en cada habitación
}



# MÉTODOS DE DETECCIÓN

st.markdown("**Elige cómo detectar el objeto:**")
metodo = st.radio("Opciones:", ['Usar la webcam', 'Subir una imagen', 'Escribir el nombre del objeto'])


if metodo == 'Usar la webcam':
    # Obtener el objeto correcto según la habitación seleccionada
    objeto_correcto = objetos_por_habitacion.get(st.session_state.habitacion, None)

    if st.session_state.habitacion == 'spacecraft':
        st.warning("🚀 En Spacecraft no necesitas mostrar ningún objeto. Solo responde las preguntas finales.")

        # Asegurar que se inicia la trivia
        if st.session_state.fase != 'trivia':
            iniciar_trivia()

    
    
    elif objeto_correcto is None:
        st.error("⚠ No hay un objeto definido para esta habitación.")
    elif st.button('Iniciar detección con cámara'):
        detectar_objeto(objeto_correcto)



elif metodo == 'Subir una imagen':
    # Obtener el objeto correcto según la habitación seleccionada
    objeto_correcto = objetos_por_habitacion.get(st.session_state.habitacion, None)

    if st.session_state.habitacion == 'spacecraft':
        st.warning("🚀 En Spacecraft no necesitas mostrar ningún objeto. Solo responde las preguntas finales.")

        # Asegurar que se inicia la trivia
        if st.session_state.fase != 'trivia':
            iniciar_trivia()

    
    elif objeto_correcto is None:
        st.error("⚠ No hay un objeto definido para esta habitación.")
    else:
        imagen_subida = st.file_uploader("📷 Sube una imagen para detectar el objeto:", type=['jpg', 'png', 'jpeg'])

        if imagen_subida is not None:
            st.image(imagen_subida, caption="Imagen subida", use_column_width=True)
            st.write("🔍 Procesando la imagen...")

            # Procesar la imagen y hacer la predicción
            img = Image.open(imagen_subida).convert('RGB')
            img = img.resize((224, 224))  
            img_array = np.array(img) / 255.0  
            img_array = np.expand_dims(img_array, axis=0)  

            # Hacer la predicción con el modelo Keras
            prediccion = modelo_keras.predict(img_array)
            clase_predicha = np.argmax(prediccion)  

            # Diccionario de clases según el modelo
            clases = {0: "airplane", 1: "banana", 2: "basketball", 3: "book", 4: "bottle", 5: "cat", 6: "cup", 7: "dog", 8: "headphones"}
            
            if clase_predicha in clases:
                objeto_detectado = clases[clase_predicha]
                st.success(f"✅ ¡Objeto detectado: {objeto_detectado}!")

                # Verificar si el objeto detectado es el correcto
                if objeto_detectado == objeto_correcto:
                    st.success(f"🎉 ¡Has detectado {objeto_detectado} correctamente!")
                    iniciar_trivia()  # Pasar a la trivia
                else:
                    st.error(f"❌ El objeto correcto en esta habitación es: {objeto_correcto}")
            else:
                st.error("⚠ No se pudo identificar el objeto.")





elif metodo == 'Escribir el nombre del objeto':
    #objeto_input = st.text_input("Escribe el nombre del objeto:")
    # Obtener el objeto correcto según la habitación seleccionada
    objeto_correcto = objetos_por_habitacion.get(st.session_state.habitacion, None)

    if st.session_state.habitacion == 'spacecraft':
        st.warning("🚀 En Spacecraft no necesitas mostrar ningún objeto. Solo responde las preguntas finales.")

        # Asegurar que se inicia la trivia
        if st.session_state.fase != 'trivia':
            iniciar_trivia()

    
    elif objeto_correcto is None:
        st.error("⚠ No hay un objeto definido para esta habitación.")
    else:
        objeto_input = st.text_input("✏ Escribe el nombre del objeto:")

        if st.button("Validar objeto") and objeto_input:
            objeto_input = objeto_input.strip().lower()  # Normalizar entrada del usuario

            if objeto_input == objeto_correcto:
                st.success(f"🎉 ¡Correcto! Has detectado un {objeto_input}.")
                st.session_state.objeto_detectado = objeto_input  
                iniciar_trivia()  # Pasar a la trivia
            else:
                st.error(f"❌ Incorrecto. El objeto esperado en esta habitación es '{objeto_correcto}'.")



# Mostrar la imagen capturada con bounding box si se detectó correctamente
if st.session_state.imagen_capturada is not None:
    st.image(st.session_state.imagen_capturada, caption="Objeto Detectado", channels='BGR', width=400)
    
# Mostrar preguntas de trivia si la fase es trivia
if st.session_state.fase == 'trivia':
    if st.session_state.trivia_index < len(st.session_state.trivia_preguntas):
        pregunta = st.session_state.trivia_preguntas[st.session_state.trivia_index]
        st.markdown(f"### {html.unescape(pregunta['question'])}")
        respuesta = st.radio("Selecciona tu respuesta:", pregunta['incorrect_answers'] + [pregunta['correct_answer']])
        if st.button('Validar'):
            st.session_state.trivia_estado_respuesta = respuesta == pregunta['correct_answer']
            if st.session_state.trivia_estado_respuesta:
                st.success("✅ ¡Correcto!")
                st.session_state.trivia_puntuacion += 1
            else:
                st.error(f"❌ Incorrecto. La respuesta correcta era: **{pregunta['correct_answer']}**")
        if st.button('Siguiente pregunta'):
            st.session_state.trivia_index += 1
            st.rerun()
