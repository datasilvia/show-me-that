

import requests
import html
import random
import sys
import time
import warnings

# Suprimir FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

###########################################
### CÓDIGO PARA LAS PREGUNTAS DE TRIVIA ###
###########################################

# Vamos a utilizar la API de OPEN TRIVIA DATABASE (https://opentdb.com/) para generar preguntas 
# aleatorias sobre categorías específicas.

def get_session_token(): # Obtenemos un nuevo token de sesión para que las preguntas no se repitan:
    response = requests.get("https://opentdb.com/api_token.php?command=request")
    if response.status_code == 200:
        data = response.json()
        if data['response_code'] == 0:
            return data['token']
    return None

def reset_session_token(token): # Cuando el token se agota y no puede dar más preguntas, se resetea:
    url = f"https://opentdb.com/api_token.php?command=reset&token={token}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        return data['response_code'] == 0  # Retorna True si el reset fue exitoso
    return False

def get_random_category_id(cat): # Para obtener preguntas sólo de la categoría genérica especificada:
    # Consultamos todas las categorías disponibles de la API.

    url = "https://opentdb.com/api_category.php"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        categories = data['trivia_categories']

    # Agrupamos las categorías de forma genérica en un diccionario:

    generic_categories = {
        'Science': [],
        'Audiovisual': [],
        'History': [],
        'Arts_and_Books': [],
        'Sports': [],
        'General_Culture': [],
        'Animals':[],
    }
    
    # Mapeamos las categorías
    category_map = {
    17: 'Science',#'Science & Nature'
    18: 'Science',#'Science: Computers'
    19: 'Science',#'Science: Mathematics'
    30: 'Science',#'Science: Gadgets'
    11: 'Audiovisual',#'Entertainment: Film'
    12: 'Audiovisual',#'Entertainment: Music'
    14: 'Audiovisual',#'Entertainment: Television'
    31: 'Audiovisual',#'Entertainment: Japanese Anime & Manga'
    32: 'Audiovisual',#'Entertainment: Cartoon & Animations'
    13: 'Audiovisual',#'Entertainment: Musicals & Theatres'
    20: 'History', #'Mythology'
    23: 'History',#'History'
    24: 'History',#'Politics'
    28: 'History',#'Vehicles'
    22: 'History',#'Geography'
    27: 'Animals',#'Animals'
    10: 'Arts_and_Books',#'Entertainment: Books'
    25: 'Arts_and_Books',#'Art'
    29: 'Arts_and_Books',#'Entertainment: Comics'
    21: 'Sports',#'Sports'
    9: 'General_Culture', # 'General Knowledge'
    26: 'General_Culture',#'Celebrities'
    15: 'General_Culture',#'Entertainment: Video Games'
    16: 'General_Culture' #'Entertainment: Board Games'
    }

    for category in categories:
        id_ = category['id']
        if id_ in category_map:
            generic_categories[category_map[id_]].append(category)
    
    # Verifica si la categoría especificada existe en el diccionario
    if cat in generic_categories:
        # Obtiene la lista de categorías para la categoría especificada
        categories = generic_categories[cat]
        
        # Elige un id aleatorio de entre las categorías especificadas
        if categories:  # Verifica que la lista no esté vacía
            random_category = random.choice(categories)
            return random_category['id']
    return None

def get_trivia_question(token, category): 
    # Establece el amount=1 para obtener solo una pregunta
    url = f"https://opentdb.com/api.php?amount=1&token={token}&category={category}"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if data['response_code'] == 0:
            question_data = data['results'][0]
            
            # Extrae la pregunta y la decodifica
            question = html.unescape(question_data['question'])
            
            # Extrae las opciones de respuesta
            options = question_data['incorrect_answers']
            options.append(question_data['correct_answer'])
            options = [html.unescape(option) for option in options]
            
            # Desordena las opciones aleatoriamente para no mostrar siempre la correcta en la misma posición
            random.shuffle(options)
            return question, options, html.unescape(question_data['correct_answer'])
        
            #Si se han agotado las preguntas y hay que resetear el token:
        elif data['response_code'] == 4:
            print("No more questions available. Reseting token")
            reset_successful = reset_session_token(token)
            if reset_successful:
                print("Token successfully reset.")
            else:
                print("Error obtaining a token for this session.")

    return 

def objeto_a_cat(objeto):# Ahora, asignaremos las categorías a objetos cotidianos, para poder implementarlas en el juego:

    objeto_categorias = {
    'Science': ['banana'],
    'Audiovisual': ['headphones'],
    'History': ['airplane'],
    'Arts_and_Books': ['book'],
    'Animals':['cat', 'dog'],
    'Sports': ['basketball'],
    'General_Culture': ['cup', 'bottle']}
    
    for category, objetos in objeto_categorias.items():
        if objeto in objetos:
            return category

def new_question(objeto):
    token = get_session_token()  # Aseguramos tener el token
    categoria = objeto_a_cat(objeto)
    category_id = get_random_category_id(categoria)

    if token:
        question, options, correct_answer = get_trivia_question(token,category_id)
        if question:
            print(f'Now get ready for a question about {categoria}!:')
            time.sleep(2)
            print(f"Question: {question}")
            time.sleep(1)
            print("Options:")
            for i, option in enumerate(options, start=1):
                print(f"{i}. {option}")

            sys.stdout.flush() # para forzar que el print se muestre antes del input!
            
            #print(f"Correct answer: {correct_answer}")  # Solo para pruebas
            time.sleep(1)
            answer = input("What's the number for the correct answer?")

            print(options[int(answer)-1])
            if options[int(answer)-1] == correct_answer:
                print("That's correct! Well done 😎")
                sys.stdout.flush()
                time.sleep(1)
                points_earned = 1
            else:
                print("I don't think so... 😓")
                print(f"My records say otherwise, the correct answer is {correct_answer}.")
                sys.stdout.flush()
                time.sleep(1)
                points_earned = 0
        else:
            print("No more questions available.")
    else:
        print("Error obtaining a token for this session.")
    return points_earned

###################################################
### CÓDIGO PARA IDENTIFICAR OBJETOS EN EL JUEGO ###
###################################################

import os
import cv2
import torch
import numpy as np
import easygui  # Para subir imágenes

def detectar_objeto(objetivo):
    """
    Permite al jugador mostrar un objeto de tres formas:
    1. Usar la webcam.
    2. Subir una imagen.
    3. Escribir el nombre del objeto.
    """
    print("\nHow will you show me the object?")
    print("1. Webcam")
    print("2. File image")
    print("3. Type manually")
    opcion = input("Please, choose an option (1, 2 o 3): ").strip()
    
    if opcion == "1":
        return detectar_objeto_camara(objetivo)
    elif opcion == "2":
        return detectar_objeto_imagen(objetivo)
    elif opcion == "3":
        return ingresar_objeto_manual(objetivo)
    else:
        print("Not valid. Please, try again.")
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
        print("Error: Webcam not available")
        return None
    
    umbral_deteccion = 5
    conteo_detectado = 0
    timing = 0
   
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
            print(f"You are showing {row['name']}")
            obj_name = row['name']
            confidence = row['confidence']
            timing +=1
            if obj_name == objetivo and confidence > 0.4:
                objeto_detectado = True
                conteo_detectado += 1
                print(conteo_detectado)
                if conteo_detectado >= umbral_deteccion:
                    print(f"{objetivo} correctly detected!")
                    cap.release()
                    cv2.destroyAllWindows()
                    return objetivo
                break
            elif timing >=300:
                print(f"{objetivo} not detected.")
                objetivo = 'Fallido'
                return objetivo 

        #cv2.imshow('Detección de Objetos - Escape Room', frame)
        #print("Use Q key to close the webcam")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
   
    return None



def detectar_objeto_imagen(objetivo):
    """
    Permite al usuario subir una imagen y detecta si el objeto está presente.
    """
    ruta_imagen = easygui.fileopenbox(title="Please choose a image file")
    if not ruta_imagen:
        print("No image chosen.")
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
            print(f"{objetivo} file image correctly detected!")
            return objetivo
    
    print("Object not detected in that file. Please, try another file.")
    return None

def ingresar_objeto_manual(objetivo):
    """
    Permite al usuario escribir el nombre del objeto manualmente.
    """
    respuesta = input(f"Please write down the object: ").strip().lower()
    sys.stdout.flush()
    if respuesta == objetivo:
        print(f"{objetivo} manually detected!")
        return objetivo
    else:
        print("That is not the target object. Please, try again.")
        return None

def predicted_object(game_state, target):
    intentos = 0
    while intentos < 3:
        objeto = detectar_objeto(target)
        #objeto = input().strip().lower()
        if objeto != target:
            intentos += 1
            if intentos < 3:
                respuesta = input("Oh, I cannot identify that object, do you want to try again? (yes/no): ").strip().lower()
                sys.stdout.flush()
                if respuesta == 'no':
                    objeto = target
                    break
        else:
            break  # Si acierta el objeto, salir del bucle
    else:
        objeto = target  # Se asigna el target después de tres intentos

    print(f"That {objeto} is jut what I needed!")
    if objeto_a_cat(objeto) not in game_state["categories_discovered"]:
        game_state["categories_discovered"].append(objeto_a_cat(objeto))
    point = int(new_question(objeto))*3
    game_state["points"] += point
    return objeto

###################################################################
### CÓDIGO PARA CREAR EL ESCAPE ROOM Y JUGAR EN CADA HABITACIÓN ###
###################################################################

from IPython.display import Image, display
import random

def linebreak():
    """
    Print a line break
    """
    print("\n")

def show_image(image_url, width=300, height=300):
  img = Image(url=image_url, width=width, height=height)
  display(img)
  time.sleep(1)

def initial_settings():
    # define game state. Do not directly change this dict.
    # Instead, when a new game starts, make a copy of this
    # dict and use the copy to store gameplay state. This
    # way you can replay the game multiple times.

    INIT_GAME_STATE = {
    "current_room": None,
    'categories_discovered': [],
    "game_over": False,
    "pet_friendly": 0,
    'points': 0,
    'all_doors': [],
    'all_objects': [],
    'all_rooms': [],
    'object_relations' : {}
    }

    game_state = INIT_GAME_STATE.copy()


    # Definimos la relación de objetos en habitaciones para la búsqueda.

    #DOORS:

    door_library = {"name": "library door",     "type": "door"}
    door_kitchen = {"name": "kitchen door",     "type": "door"}
    door_living = {"name": "living room door",  "type": "door"}
    door_bedroom = {"name": "bedroom door",     "type": "door"}
    door_outside = {"name": "outside door",     "type": "door"}
    all_doors = [door_library, door_kitchen, door_living, door_bedroom, door_outside]

    #FURNITURE:

    cup =        {"name": "cup",        "type": "furniture"}
    bottle =     {"name": "bottle",     "type": "furniture"}
    headphones = {"name": "headphones", "type": "furniture"}
    book =       {"name": "book",       "type": "furniture"}
    banana =     {"name": "banana",     "type": "furniture"}
    cat =        {"name": "cat",        "type": "furniture", 'category': 'Animals'}
    dog =        {"name": "dog",        "type": "furniture", 'category': 'Animals'}
    basketball = {"name": "basketball", "type": "furniture"}
    airplane =   {"name": "airplane",   "type": "furniture"}
    spacecraft = {"name": "Charlie's spacecraft", "type": "spacecraft"}
    all_objects = [airplane, banana, basketball, book, bottle, cat, cup, dog, headphones]

    #ROOMS:

    hall = {
        "name": "hall",
        "type": "room",
        "image": 'url',
        "category": "General_Culture",
        "target": [cat,dog],
    }

    library = {
        "name": "library",
        "type": "room",
        "image": 'url',
        "category": 'Arts_and_Books',
        "target": [book],
        "clue": 'One of those blocks in the shelf would help me. Can you give one to me?',
    }

    kitchen = {
        "name": "kitchen",
        "type": "room",
        "image": 'url',
        "category": 'Science',
        "target": [banana],
        "clue": "My color is yellow, and I grow on trees, I'm a popular food with apes and monkeys"
    }

    living_room = {
        "name": "living room",
        "type": "room",
        "image": 'url',
        "category": 'History',
        "target": [airplane],
        "clue": 'What a beautiful model! Is that an Airbus A350? Show it to me, please!'
    }

    bedroom = {
    "name": "bedroom",
    "type": "room",
    "image": 'url',
    "category": 'Audiovisual',
    "target": [headphones],
    "clue": 'I love listening to music, do you have any item to help me listening to it without bothering anyone else?',
    }

    outside = {
    "name": "outside",
    "type": "room",
    "image": 'url',
    "category": 'Sports',
    "target": [basketball],
    "clue": 'It is important to do some exercise before a long trip. Wanna try some shots?'
    }

    space = {
    "name": "outer space",
    "type": "room",
    "image": 'url',
    }

    #Delimitar habitaciones:

    all_rooms = [hall, library, kitchen, living_room, bedroom, outside]

    # define which items/rooms are related

    object_relations = {
        ### ROOMS
        "hall": [door_library, door_kitchen, door_living, door_bedroom, door_outside],
        "library": [book,  door_library],
        "kitchen": [banana, door_kitchen],
        "living room": [airplane, door_living],
        "bedroom": [headphones, door_bedroom],
        "outside": [basketball, door_outside, spacecraft],
        ### DOORS
        "library door": [hall, library],
        "kitchen door": [hall, kitchen],
        "living room door": [hall, living_room],
        "bedroom door": [hall, bedroom],
        "outside door": [hall, outside],
    }

    game_state['all_doors'].append(all_doors)
    game_state['all_rooms'].append(all_rooms)
    game_state['all_objects'].append(all_objects)
    game_state['object_relations'] = object_relations
    game_state['current_room'] = all_rooms[0]
    return game_state

def play_room(game_state, room):
    """
    Play a room. First check if the room being played is the target room.
    If it is, the game will end with success. Otherwise, let player either
    explore (list all items in this room) or examine an item found here.
    """

    game_state["current_room"] = room

    if game_state["game_over"] == True:
        print('Yayyyy! You helped Charlie repair the spaceship, and you learnt a lot in the process.')
        print('Thank you very much for your help!')
    else:
        print("You are now in the " + room["name"])
        #show_image(room["image"])
        
        if room["name"] == "hall":
            game_state["pet_friendly"] += 1
            if game_state["pet_friendly"] == 3:
                pet_friendly(game_state)

        
        if room["category"] not in game_state["categories_discovered"]:
            print(room["clue"])

            objeto = room['target'][0]['name']  # Obtener el nombre del objeto esperado
            objeto_detectado = predicted_object(game_state, objeto)
        
        intended_action = input("What would you like to do? Type 'explore' or 'examine'?").strip()
        sys.stdout.flush()
        print(intended_action)
        sys.stdout.flush()
        if intended_action == "explore":
            explore_room(game_state, room) 
        elif intended_action == "examine":
            sys.stdout.flush()
            item_to_examine = input("What would you like to examine?").strip()
            sys.stdout.flush()
            examine_item(game_state, item_to_examine)
        else:
            print("Not sure what you mean. Type 'explore' or 'examine'.")
            play_room(game_state, room)

        linebreak()

def explore_room(game_state, room):
    """
    Explore a room. List all items belonging to this room.
    """
    items = [i["name"] for i in game_state['object_relations'][room["name"]]]
    print("You explore the room. This is the " + room["name"] + ". You find a " + ", ".join(items))
    play_room(game_state, room)
    return 

def examine_item(game_state, item_name):
    """
    Examine an item which can be a door or furniture.
    First make sure the intended item belongs to the current room.
    Then check if the item is a door. Ask player if they want to go to the next
    room. If the item is not a door, then a trivia question is asked.
    """
    current_room = game_state["current_room"]
    next_room = ""
    output = None
    for item in game_state['object_relations'][current_room["name"]]:
        if(item["name"] == item_name):
            output = "You examine " + item_name + ". "
            #Si el objeto es igual puerta
            if(item["type"] == "door"):
                output += "You unlock it."
                print(output)
                next_room = get_next_room_of_door(item, current_room, game_state)
            elif(item["type"] == "spacecraft"):
                game_state["game_over"] = end_game(game_state)
            else:
                print(output)
                sys.stdout.flush() # para que el print se ejecute antes del input
                
                point = int(new_question(item_name))
                game_state["points"] += point
                if item_name == "cat" or item_name == "dog":
                    print("Awwww it is so flufflyyyyyy 😍😍😍😍😍")
            break
    if(output is None):
        print("The item you requested is not found in the current room.")
    if(next_room and input("Do you want to go to the next room? Type 'yes' or 'no'").strip() == 'yes'):
        play_room(game_state, next_room)
    else:
        play_room(game_state, current_room)

def pet_friendly(game_state):

    print('By the way, I love animals, are you a cat or a dog person?')
    animalito = input('Please write cat or dog').strip().lower()
    print(f'Oh! is that your {animalito}?')
    print('Awwwwwwwww 😍😍😍')
    print('Can you show me your fluffy friend more closely?')
    sys.stdout.flush() # Para que el print aparecza antes del input
    
    predicted_object(game_state, animalito)
    animalito = {"name": animalito, "type": "pet"}
    game_state['object_relations']["hall"].append(animalito)
    return 
    

def start_game(game_state):
    print('Hey! Hey!')
    print('Are you OK?')
    print('Come on, wake up!')
    show_image('https://img.freepik.com/vector-premium/linda-ilustracion-alienigena-que-agita_723554-82.jpg?w=2000')
    print('I am X4R-L1, but my friends call me Charlie 😊')
    linebreak()
    print('I need your help, my flying saucer crashed between Orion and Sirius.')
    print("I tried hitchhiking, but I stumbled into a black hole and that's how I landed on top on you 😁")
    print('I need several objects to repair my ship, could you help me?')
    linebreak()
    print("Also, I'm a bit thirsty... do you have any bottle to drink?")
    
    objeto = predicted_object(game_state, 'bottle')
    #print('...')
    
    print("Now, let's go into your house!")

    play_room(game_state, game_state["current_room"])
    
    

def get_next_room_of_door(door, current_room, game_state):
    """
    From object_relations, find the two rooms connected to the given door.
    Return the room that is not the current_room.
    """
    connected_rooms = game_state['object_relations'][door["name"]]
    next_room = next(room for room in connected_rooms if room != current_room)

    return next_room

def final_test(game_state):
    token = get_session_token()  # Aseguramos tener el token
    print("Get ready for the final test!")
    final_points = game_state["points"]
    print(f"This is your current score: {final_points}")
    print("Will you beat it?")
    if token:
        for category in game_state["categories_discovered"]:
            category_id = get_random_category_id(category)
            result = get_trivia_question(token, category_id)
            if result is not None:  # Verifica que el resultado no es None antes de desempacar
                question, options, correct_answer = result
                
                print(f'Now get ready for a question about {category}!:')
                print(f"Question: {question}")
                print("Options:")
                for i, option in enumerate(options, start=1):
                    print(f"{i}. {option}")

                sys.stdout.flush() # Para forzar que el print se ejecute antes que el input   
                
                #print(f"Correct answer: {correct_answer}")  # Solo para pruebas
                answer = input("What's the number for the correct answer?")

                print(options[int(answer)-1])
                if options[int(answer)-1] == correct_answer:
                    print("That's correct! Well done 😎")
                    final_points += 10
                else:
                    print("I don't think so... 😓")
                    print(f"My records say otherwise, the correct answer is {correct_answer}.")
                    final_points += 0
            else:
                final_points += 0
        output = print(f"Well done! This is your final score: {final_points}")
    else:
        print("Error obtaining a token for this session.")
        return output


def end_game(game_state):
    print("This is Charlie's spacecraft.")
    num_items = len(game_state["categories_discovered"])
    if num_items < 7:
        print(f"You have scored {game_state["points"]} so far!")
        print("There are yet some items to collect, do you want to keep playing?")
        keep_playing = input("Type yes or no").strip().lower()
        if keep_playing == "yes":
            game_over = False
        else:
            game_over = True    
    elif num_items == 7:
        print("Way to go! All the items are collected.")
        print(f"You have scored {game_state["points"]} so far!")
        print("Are you ready for the final test?")
        keep_playing = input("Type yes or no").strip().lower()
        if keep_playing == "yes":
            final_test(game_state)
            game_over = True
        else:
            print("Do you want to keep playing?")
            keep_playing = input("Type yes or no").strip().lower()
            if keep_playing == "yes":
                game_over = False
            else:
                game_over = True
    return game_over            
