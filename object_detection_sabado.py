import os
import cv2
import torch
import numpy as np
import time
import easygui  # Para subir imágenes

def detectar_objeto(objetivo):
    """
    Permite al jugador mostrar un objeto de tres formas:
    1. Usar la webcam.
    2. Subir una imagen.
    3. Escribir el nombre del objeto.
    """
    print("\n¿Cómo quieres mostrar el objeto?")
    print("1. Usar la webcam")
    print("2. Subir una imagen")
    print("3. Escribirlo manualmente")
    opcion = input("Selecciona una opción (1, 2 o 3): ").strip()
    
    if opcion == "1":
        return detectar_objeto_camara(objetivo)
    elif opcion == "2":
        return detectar_objeto_imagen(objetivo)
    elif opcion == "3":
        return ingresar_objeto_manual(objetivo)
    else:
        print("Opción no válida. Intenta de nuevo.")
        return detectar_objeto(objetivo)



def detectar_objeto_camara(objetivo):
    """
    Abre la webcam y detecta si el objeto especificado aparece en pantalla.
    Solo valida el objeto pasado como argumento.
    Si se detecta de forma estable en 5 frames consecutivos, confirma la detección.
    """
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.to('cpu')
    model.eval()

   

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo acceder a la webcam")
        return None
    
    umbral_deteccion = 5
    conteo_detectado = 0
   
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame = cv2.resize(frame, (320, 240))
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = model(img_rgb)
        detections = results.pandas().xyxy[0]
        
        objeto_detectado = False
        for _, row in detections.iterrows():
            print(f"{row['name']}")
            print(f"{row['confidence']}")
            obj_name = row['name']
            confidence = row['confidence']
            
            if obj_name == objetivo and confidence > 0.5:
                objeto_detectado = True
                break
            
      
        if objeto_detectado:
            conteo_detectado += 1
            print(conteo_detectado)
        else:
            conteo_detectado = max(0, conteo_detectado - 1)
            
            break
        
        if conteo_detectado >= umbral_deteccion:
            print(f"¡{objetivo} detectado de forma estable!")
            cap.release()
            cv2.destroyAllWindows()
            return objetivo

        #cv2.imshow('Detección de Objetos - Escape Room', frame)
        print("pulsar q para cerrar")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
   
    cap.release()
    cv2.destroyAllWindows()
    return None



def detectar_objeto_imagen(objetivo):
    """
    Permite al usuario subir una imagen y detecta si el objeto está presente.
    """
    ruta_imagen = easygui.fileopenbox(title="Selecciona una imagen del objeto")
    if not ruta_imagen:
        print("No se seleccionó ninguna imagen.")
        return None
    
    model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True)
    model.to('cpu')
    model.eval()
    
    img = cv2.imread(ruta_imagen)
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    results = model(img_rgb)
    detections = results.pandas().xyxy[0]

    for _, row in detections.iterrows():
        if row['name'] == objetivo and row['confidence'] > 0.5:
            print(f"¡{objetivo} detectado en la imagen!")
            return objetivo
    
    print("No se detectó el objeto en la imagen. Intenta con otra.")
    return None

def ingresar_objeto_manual(objetivo):
    """
    Permite al usuario escribir el nombre del objeto manualmente.
    """
    respuesta = input(f"Escribe el nombre del objeto ({objetivo}): ").strip().lower()
    if respuesta == objetivo:
        print(f"¡{objetivo} validado manualmente!")
        return objetivo
    else:
        print("El objeto ingresado no es correcto. Intenta de nuevo.")
        return None

