import streamlit as st
import cv2
import torch
import requests
import html
import random
import numpy as np
import pandas as pd

# Configuración de la página (debe ser el primer comando de Streamlit)
st.set_page_config(page_title='Escape Room Trivia', page_icon='🧩', layout='centered')

st.title('🔐 Escape Room Trivia')

# Introducción narrativa
st.markdown('''
## Despiertas en un lugar desconocido...
Para escapar, debes resolver acertijos y mostrar ciertos objetos a la cámara.

### Primer acertijo: 
"¿Qué es algo que contiene líquido y es esencial para la vida?"

¡Enseña una **botella** a la cámara para continuar!
''')


# Estado inicial
def init_session_state():
    if 'fase' not in st.session_state:
        st.session_state.fase = 'inicio'
    if 'trivia_preguntas' not in st.session_state:
        st.session_state.trivia_preguntas = []
        st.session_state.trivia_index = 0
        st.session_state.trivia_puntuacion = 0
        st.session_state.trivia_respuesta_usuario = None
        st.session_state.trivia_estado_respuesta = None
    if 'camara_activa' not in st.session_state:
        st.session_state.camara_activa = False
    if 'imagen_capturada' not in st.session_state:
        st.session_state.imagen_capturada = None
    if 'botella_detectada' not in st.session_state:
        st.session_state.botella_detectada = False

init_session_state()

# Cargar modelos YOLOv5
@st.cache_resource  
def cargar_modelos():
    model_yolo = torch.hub.load('./yolov5', 'custom', path='yolov5/yolov5s.pt', source='local')
    model_custom = torch.hub.load('./yolov5', 'custom', path='yolov5/best.pt', source='local')
    return model_yolo, model_custom

model_yolo, model_custom = cargar_modelos()

def get_trivia_questions(amount=3, category=9):
    url = f"https://opentdb.com/api.php?amount={amount}&category={category}&type=multiple"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()['results']
    return []

def detectar_objeto(objeto):
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        st.error('No se pudo acceder a la cámara. Asegúrate de que no está en uso por otra aplicación.')
        st.stop()

    stframe = st.empty()
    frame_count = 0  # Contador de frames consecutivos
    max_frames = 5  # Frames consecutivos necesarios

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
            conf = row['confidence']
            label = f"{objeto.capitalize()} {conf:.2f}"
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        stframe.image(frame, channels='BGR', use_column_width=True)
        
        if not detecciones.empty:
            frame_count += 1
            st.info(f'{objeto.capitalize()} detectado {frame_count}/{max_frames} frames seguidos')
        else:
            frame_count = 0  
    
    cap.release()
    cv2.destroyAllWindows()
    st.session_state.imagen_capturada = frame
    st.session_state.botella_detectada = True
    st.session_state.fase = 'confirmacion'
    st.rerun()

def realizar_trivia(categoria):
    st.session_state.trivia_preguntas = get_trivia_questions(amount=3, category=categoria)
    st.session_state.trivia_index = 0
    st.session_state.fase = 'trivia'
    st.rerun()

if st.session_state.fase == 'inicio':
    if st.button('Activar cámara para detectar botella') and not st.session_state.camara_activa:
        st.session_state.fase = 'deteccion_botella'
        st.rerun()

elif st.session_state.fase == 'deteccion_botella':
    detectar_objeto('bottle')

elif st.session_state.fase == 'confirmacion':
    st.image(st.session_state.imagen_capturada, channels='BGR', use_column_width=True, caption='Imagen capturada')
    st.success('¡Enhorabuena, has acertado!')
    if st.button('Continuar'):
        realizar_trivia(9)

elif st.session_state.fase == 'trivia':
    if st.session_state.trivia_index < len(st.session_state.trivia_preguntas):
        pregunta_actual = st.session_state.trivia_preguntas[st.session_state.trivia_index]
        st.markdown(f"### {html.unescape(pregunta_actual['question'])}")
        opciones = pregunta_actual['incorrect_answers'] + [pregunta_actual['correct_answer']]
        random.shuffle(opciones)

        respuesta = st.radio("Selecciona tu respuesta:", opciones, key=f"q{st.session_state.trivia_index}")

        if st.button('Validar respuesta'):
            if respuesta == pregunta_actual['correct_answer']:
                st.success("✅ ¡Correcto!")
                st.session_state.trivia_puntuacion += 1
            else:
                st.error("❌ Incorrecto.")
            
            st.session_state.trivia_index += 1
            st.rerun()
    else:
        st.markdown(f"### 🎯 Puntuación final: {st.session_state.trivia_puntuacion}/{len(st.session_state.trivia_preguntas)}")
        if st.button('Volver al inicio'):
            st.session_state.fase = 'inicio'
            st.session_state.trivia_index = 0
            st.session_state.trivia_puntuacion = 0
            st.rerun()
