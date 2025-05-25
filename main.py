import functions_framework
import json
import openai
import os
import ast
from flask import Response, send_file
from google.cloud import firestore
from google.oauth2 import id_token
from google.auth.transport import requests
import logging
from OpenAI_model import *
import random, json
from datetime import datetime
from zoneinfo import ZoneInfo
import io
from io import BytesIO
import requests as rq
from utils import *

openai.api_key = os.getenv("OPENAI_API_KEY")
GOOGLE_OAUTH2_CLIENT_ID = os.getenv("GOOGLE_OAUTH2_CLIENT_ID")
db = firestore.Client(project=os.getenv("PROJECT_ID"))

headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*"
}

system_prompt_dict={'week1':"""You are a practice assistant called Pierre for an introductory French course. The session plan for this week focuses on French sounds, accents, the alphabet, and formalities (merci, de rien, s'il vous plaît). The suggested vocabulary to focus on contains the following phrases: ["Bonjour", "comment allez vous?", "comment ça va ?", "Je m'appelle...", "Merci beaucoup", "De rien", "S'il vous plaît", "Excusez-moi", "Ça va bien", "Ça va mal", "Comment tu t'appelles?","Comment vous vous appellez?", "À bientôt", "Bonne journée", "Au Revoir"]. Have a practice conversation with the student staying as close to the listed vocabulary and course plan as possible. Use as basic and simple vocabulary and sentence structures as possible; no more than 8 French Words in the response. Keep consistent the level of formality required in the conversation (tu/vous, etc.), gender, based on the user's responses. Keep consistent the level of formality required in the conversation (tu/vous, comment ca va/comment allez-vous etc.), and gender of words, based on the user's responses. Must avoid idioms, slang, and complex grammatical constructs. Do not translate any French phrases in your response into English.  Do not correct the user's errors. Keep the conversation going.""",
                    'week2':"""You are a practice assistant called Pierre for an introductory French course. The session plan for this week focuses on French Greetings, personal pronouns (tu/vous), instructions (répétez, écoutez, parlez, lisez, plus fort, lentement, épeler), introductory sentences (je m'appelle…, je suis…indien/indienne, j'habite à…), present tense of the verb s'appeler, nouns, and gender. The suggested vocabulary to focus on contains the following phrases: ["Bonjour", "comment ça va ?", "comment allez vous?", "Je m'appelle...", "Merci beaucoup", "De rien", "S'il vous plaît", "Excusez-moi", "Ça va bien", "Ça va mal", "Comment tu t'appelles?","Comment vous vous appellez?","Vous pouvez épeler?", "Je suis étudiant","Je suis étudiante", "J'habite à...", "Je suis de...", "Parlez-vous anglais?", "Je ne comprends pas", "Pouvez-vous répéter ?", "Parlez plus lentement", "Je voudrais...", "Comment dit-on... en français ?", "J'ai une question", "Où est... ?", "C'est combien ?", "Je ne sais pas", "Je suis désolé(désolée)", "À bientôt", "Bonne journée", "Au Revoir"]. Have a practice conversation with the student staying as close to the listed vocabulary and course plan as possible. Use as basic and simple vocabulary and sentence structures as possible; no more than 10 French Words in the response. Keep consistent the level of formality required in the conversation (tu/vous, comment ca va/comment allez-vous etc.), and gender of words, based on the user's responses. Must avoid idioms, slang, and complex grammatical constructs. Do not translate any French phrases in your response into English.  Do not correct the user's errors. Keep the conversation going.""",
                    'week3':"""You are a practice assistant called Pierre for an introductory French course. The session plan for this week focuses on French Definite-Indefinite Articles (un, une, des, le, la, l', les). The suggested vocabulary to focus on contains the following words and phrases: ["Un", "Une", "Des", "Le", "La", "L'", "Les", "J'habite à...", "Je suis de...", "Comment dit-on... en français?", "À bientôt", "Au Revoir", "Bonne journée"]. Have a practice conversation with the student, nudging them to stay as close to the listed vocabulary and course plan as possible, discuss the articles in diverse contexts. Use as basic and simple vocabulary and sentence structures as possible; no more than 12 French Words in the response. Keep consistent the level of formality required in the conversation (tu/vous, comment ca va/comment allez-vous etc.), and gender of words, based on the user's responses. Must avoid idioms, slang, and complex grammatical constructs. Do not translate any French phrases in your response into English.  Ignore the user's errors. Keep the conversation going.""",
                    'week4':"""You are a practice assistant called Pierre for an introductory French course. The session plan for this week focuses on French Verb être Countries/Nationalities (prepositions + city / country à, au, en, aux). The suggested vocabulary to focus on contains the following phrases: ["Un", "Une", "Des", "Le", "La", "L'", "Les", "Être", "Je suis", "Tu es", "Il est", "Elle est", "Nous sommes", "Vous êtes", "Ils sont", "Elles sont", "À", "Au", "En", "Aux", "Pays", "Ville", "Français", "Française", "Américain", "Américaine", "Espagnol", "Espagnole", "Allemand", "Allemande", "Italien", "Italienne", "Chinois", "Chinoise","Canadien", "Canadienne", "Anglais", "Anglaise", "Japonais", "Japonaise", "le France", "les États-Unis", "l'Espagne", "l'Allemagne", "l'Italie", "la Chine", "le Canada", "l'Angleterre", "le Japon", "le Pakistan", "le Bangladesh", "l'Inde","Pakistanais", "Pakistanaise", "Bangladais","Bangladaise", "Indien", "Indienne", "Bonjour", "Comment ça va ?", "Comment dit-on... en français?", "Au Revoir"]. Have a practice conversation with the student staying as close to the listed vocabulary and course plan as possible. Use as basic and simple vocabulary and sentence structures as possible; no more than 14 French Words in the response. Keep consistent the level of formality required in the conversation (tu/vous, comment ca va/comment allez-vous etc.), and gender of words, based on the user's responses. Must avoid idioms, slang, and complex grammatical constructs. Do not translate any French phrases in your response into English.  Do not correct the user's errors. Keep the conversation going."""
            }


def update_timestamps(doc, jti):
    data = doc.get().to_dict()
    current_timestamps = data[jti]['timestamp']
    current_timestamps[1] = datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d_%H-%M-%S")
    logging.warning(f'updated timestamp to {current_timestamps}')
    doc.update({
            f'{jti}.timestamp': current_timestamps
        })
    pass


def login(id_info):
    collection = db.collection(os.getenv("COLLECTION_NAME"))
    logging.warning(f"id_info: {id_info}")

    username = id_info.get("email").replace('@flame.edu.in','')
    jti = id_info.get("jti")
    documents = collection.document(username)
    logging.warning(f"username: {username}")
    # if not documents:
    #     return Response(json.dumps({"error": "You are not authorised."}), status=401, mimetype='application/json', headers=headers)
    doc = documents.get()
    if not doc.exists:
        data = {'name': id_info.get('name'),'privacy': 1, jti:{'timestamp':[datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d_%H-%M-%S"),datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d_%H-%M-%S")],'CC':[], 'MM':{'score':0, 'high_score':0, 'correct_answers':[], 'incorrect_answers':[]}, 'VV':{'seen_words':[]}}}
        documents.set(data)
        logging.warning(f"documents set for first time: {doc.to_dict()}")
    
    # else if documents exists:

    documents.update({jti:{'timestamp':[datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d_%H-%M-%S"),datetime.now(tz=ZoneInfo('Asia/Kolkata')).strftime("%Y-%m-%d_%H-%M-%S")],'CC':[], 'MM':{'score':0, 'high_score':0, 'correct_answers':[], 'incorrect_answers':[]}, 'VV':{'seen_words':[]}}})
    logging.warning(f"documents already there: {documents.get().to_dict()}")
    return {
        "email": id_info.get("email"), 
        "name": id_info.get("name"), 
        "picture": id_info.get("picture")
    }

def chat(request, doc, jti):
    try:
        # print(request)
        logging.warning("Input Request Format: %s", request)
        data = json.loads(request.data)
        user_message = data.get('messages', [])[1:]
        logging.warning("Data Format: %s", data.get('week'))
        week = data.get('week')
        logging.warning("User Message Format: %s", user_message)
        for item in user_message:
            if item['role'] == 'assistant':
                for i in item['content']:
                    if '[Response]' in i:
                        logging.warning(f'line 82 item content: {i.encode().decode("unicode_escape").lstrip("[Response] ")}')
                        item['content'] = " ".join([t[0] for t in ast.literal_eval(i.encode().decode('unicode_escape').lstrip("[Response] ").replace("\\\"","'").replace("\\","").strip('"'))])

        logging.warning("User Message Format: %s", user_message)
        # print(user_message)
        chatbot = OpenAIBot("French", "English")
        # set system prompt
        chatbot.system_prompt = (system_prompt_dict[week])
        chatbot.conversation_history = [{
            "role": "system",
            "content": chatbot.system_prompt
        }]
        # add all messages into user_message.
        chatbot.conversation_history.extend(user_message)
        logging.warning("line 80 chaybot.convhistory: %s", chatbot.conversation_history)
        # add_message("user", user_message)
        response_content = chatbot.generate_response(user_message[-1]['content'])
        # print(response_content)
        logging.warning("line 84 Response Content: %s", response_content)
        correction = chatbot.correct_user(user_message[-1]['content'])
        # print(correction, response_content)
        full_trans = chatbot.full_translation(response_content)
        logging.warning("line 88 full trans: %s", full_trans)
        # Convert response_content to list of tuples
        word_translations = chatbot.language_breakdown(response_content)
        logging.warning("line 91 Response Content: %s", word_translations)

        if(correction.lower().replace('.','') =='correct'):
            correction = ''
        logging.warning("line 95 correction: %s", correction)
        logging.warning("line 96 jsondumps: %s", json.dumps(word_translations))
        
        # When a correction is made
        if(correction != ''):
            response_list = [
                f"[Correction] {correction}",
                f"[Response] {json.dumps(word_translations)}",  # Serialize the list of tuples
                f"[Translation] {full_trans}"
            ] 
            db_data_list = [{
            'user_response': user_message[-1]['content'], 
            'assistant_response': {'correction': correction, 'response': response_content, 'translation': full_trans},
            'week': week,
            'asr': {'wrong_attempts':0, 'closed': 0}
                        }]

            logging.warning(f"response_list line 130 {response_list}")

            # db update:
            doc.update({f"{jti}.CC": firestore.ArrayUnion(db_data_list)})
            logging.warning(f"chat databse update: {doc.get().to_dict()[jti]}")

            print(f'Line 139: ASR: {process_correction_string(correction)}')

            return {"role": "assistant", "content": response_list, "asr": process_correction_string(correction)}

        # When no correction is needed
        else: 
            response_list = [
            f"[Response] {json.dumps(word_translations)}",  # Serialize the list of tuples
            f"[Translation] {full_trans}"]

            db_data_list = [{
            'user_response': user_message[-1]['content'], 
            'assistant_response': {'response': response_content, 'translation': full_trans},
            'week': week
                        }]

            # db update:
            doc.update({f"{jti}.CC": firestore.ArrayUnion(db_data_list)})
            logging.warning(f"chat databse update: {doc.get().to_dict()[jti]}")

            logging.warning(f"response_list line 149 {response_list}")

            return {"role": "assistant", "content": response_list, "asr": ""}

    except Exception as e:
        logging.warning(f'error::::  {e}')
        return {"error": e}

basic_words = {
    'week1': [
        ("De rien", "welcome"), ("S'il vous plaît", "please"), ("Bonjour", "hello"),
        ("Au revoir", "goodbye"), ("Bonsoir", "good evening"), ("Salut", "hi"),
        ("À bientôt", "see you soon"), ("À demain", "see you tomorrow"),
        ("Excusez-moi", "excuse me"), ("Pardon", "sorry"), ("Comment", "how"),
        ("Très bien", "very well"), ("Bien", "well")
    ],

    'week2': [
        ("Tu", "you (informal singulier)"), ("Vous", "you (formal singulier/pluriel)"), ("Répétez", "repeat"),("Écoutez", "listen"),
        ("Parlez", "speak"), ("Lisez", "read"),("Fort", "loud"), ("Lentement", "slowly"),
        ("Je", "I"),("Appeler", "call"), ("Nom", "name"), ("Genre", "gender"),("Masculin", "masculine"), 
        ("Féminin", "feminine"), ("Habiter", "live"), ("Merci", "thank you")
        ],

    'week3': [
        ("Un", "a (masculin, singulier)"), ("Une", "a (feminin, singulier)"), ("Des", "some (masculin/feminin, pluriel)"), ("Le", "the (masculin, singulier)"), ("La", "the (feminin, singulier)"), 
        ("L’", "the (masculin/feminin, singulier)"), ("Les", "the (masculin/feminin, pluriel)"), ("Répétez", "repeat"),("Écoutez", "listen"),
        ("Parlez", "speak"), ("Lisez", "read"),("Fort", "loud"), ("Lentement", "slowly"),
        ("L'acteur", "actor (m.)"), ("L'hôtel", "hotel (m.)"),("Le film", "film (m.)"),
        ("Le directeur", "director (m.)"),("Le cinéma", "cinema (m.)"), ("Le palais", "palace (m.)"), ("La mer", "sea (f.)"),
        ("Je", "I"),("Appeler", "call"), ("Vous","you (formal/pluriel)"), ("Nous","we"), ("Ils","they (masculin pluriel)"), ("Elles", "they (feminin, pluriel)")
    ], 
    
    'week4': [
        ("Être", "to be"), ("Je suis", "I am"), ("Tu es", "you are (informal)"),
        ("Il est", "he is"),("Elle est", "she is"),("Nous sommes", "we are"),
        ("Vous êtes", "you are (formal/plural)"),("Ils sont", "they are (masculin)"),("Elles sont", "they are (feminin)"),
        ("À la", "to (feminin singulier)"),("Au", "to (masculin singulier)"),
        ("En", "in"), ("Aux", "to (plural)"),("La ville", "city"),("Le Français", "French (m.)"),
        ("La Française", "French (f.)"),("L'Indien", "Indian (m.)"),("L'Indienne", "Indian (f.)"),
        ("L'Américain", "American (m.)"),("L'Américaine", "American (f.)"),("L'Espagnol", "Spanish (m.)"),
        ("L'Espagnole", "Spanish (f.)"),("L'Allemand", "German (m.)"),("L'Allemande", "German (f.)"),
        ("L'Italien", "Italian (m.)"),("L'Italienne", "Italian (f.)"),("Le Chinois", "Chinese (m.)"),
        ("La Chinoise", "Chinese (f.)"),("Le Canadien", "Canadian (m.)"),("La Canadienne", "Canadian (f.)"),
        ("L'Anglais", "English (m.)"),("L'Anglaise", "English (f.)"),("Le Japonais", "Japanese (m.)"),
        ("La Japonaise", "Japanese (f.)"),("La France", "France (f.)"),("L'Inde", "India (f.)"),
        ("Les États-Unis", "United States (m.)"),("L'Espagne", "Spain (f.)"),("L'Allemagne", "Germany (f.)"),
        ("L'Italie", "Italy (f.)"),("La Chine", "China (f.)"),("Le Canada", "Canada (m.)"),
        ("L'Angleterre", "England (f.)"),("Le Japon", "Japan (m.)"),("Le Pakistan", "Pakistan (m.)"),
        ("Le Bangladesh", "Bangladesh (m.)"),("L'Algérie", "Algeria (f.)"),("Le Maroc", "Morocco (m.)"),
        ("La Tunisie", "Tunisia (f.)"),("Le Sénégal", "Senegal (m.)"),("Le Vietnam", "Vietnam (m.)"),
        ("La Côte d'Ivoire", "Ivory Coast (f.)"),("Le Madagascar", "Madagascar (m.)"),("Le Mali", "Mali (m.)")
    ]
                }


grammar_games_dict = {
    'week1': [
        ('Rearrange the jumbled words to form a correct sentence: <br> <b>vous, allez, ?, comment</b>','Comment allez-vous?'), ('Rearrange the jumbled words to form a correct sentence: <br> <b> m’appelle, je, Lily</b>','Je m’appelle Lily'), ('Rearrange the jumbled words to form a correct sentence: <br> <b> bien, ça, va</b>', 'Ça va bien'), ('Rearrange the jumbled words to form a correct sentence: <br> <b> vous, comment, ?, appellez, vous</b>','Comment vous vous appellez?'),
        ('Identify the word or phrase that doesn’t belong in the group <b>À demain, Au revoir, À bientôt, Comment ça va?</b>', 'Comment ça va?'), ('Identify the word or phrase that doesn’t belong in the group <b> Ça va bien, Ça va mal, Je vais bien, Bonjour</b>','Bonjour'),
        ("Enter the meaning of the word <b>Merci</b>", "thank you"), ("Enter the meaning of the word <b>De rien</b>", "welcome"), ("Enter the meaning of the word <b>S'il vous plaît</b>", "please"), ("Enter the meaning of the word <b>Bonjour</b>", "hello"),
        ("Enter the meaning of the word <b>Au revoir</b>", "goodbye"), ("Enter the meaning of the word <b>Bonsoir</b>", "good evening"), ("Enter the meaning of the word <b>Salut</b>", "hi"), ("Enter the meaning of the word <b>À bientôt</b>", "see you soon")
    ],
    'week2': [
        ('Rearrange the jumbled words to form a correct sentence: <br> <b>journée, beaucoup, et, Merci, bonne</b>','Merci beaucoup et bonne journée.'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>je, Excusez, suis, moi, désolé</b>','Excusez-moi, je suis désolé'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>comment, Je, toi, m’appelle, tu, Sophie, et, t’appelles</b>','Je m’appelle Sophie, et toi, comment tu t’appelles'),
        ('Identify the word or phrase that doesn’t belong in the group  <b>Bonjour, Bonsoir, Bonne Nuit, Comment ça va?</b>','Comment ça va?'),
        ('Enter the meaning of the word: <b>Répétez</b>','Repeat'), ('Enter the meaning of the word: <b>Écoutez</b>','listen'), ('Enter the meaning of the word: <b>Parlez</b>','speak'), ('Enter the meaning of the word: <b>Lisez</b>','read'),
        ('Enter the meaning of the word: <b>Lentement</b>','slowly'), ('Enter the meaning of the word: <b>Fort</b>','loud'), ('Enter the meaning of the word: <b>Habiter</b>','live'), ('Enter the meaning of the word: <b>Comment</b>','how')
    ],
    'week3': [
        ('Rearrange the jumbled words to form a correct sentence: <br><b>suis, de, Je, Lyon</b>','Je suis de Lyon'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>voiture, rouge, est, la</b>','La voiture est rouge'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>bleu, est, livre, le</b>','Le livre est bleu'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>table, grande, est, la</b>','La table est grande'),
        ('Identify the word or phrase that doesn’t belong in the group: <b>Un, Une, Le, Des</b>','Le'), ('Identify the word or phrase that doesn’t belong in the group: <b>L’, Une, Le, Les</b>','une'), ('Identify the word or phrase that doesn’t belong in the group: <b>Au Revoir, Bonne journée, À bientôt, Des</b>','Des'), 
        ('Enter the meaning of the word: <b>Un</b>','a'), ('Enter the meaning of the word: <b>Des</b>','some'), ('Enter the meaning of the word: <b>Le</b>','the'), ('Enter the meaning of the word: <b>L’</b>','the'),
        ('Guess the correct indefinite article for: <b>Livre</b>','un'), ('Guess the correct indefinite article for: <b>Fille</b>','une'), ('Guess the correct indefinite article for: <b>Amis</b>','des'), ('Guess the correct indefinite article for: <b>Maison</b>','une'),
        ('Guess the correct definite article for: <b>Chien</b>','le'), ('Guess the correct definite article for: <b>École</b>','l’'), ('Guess the correct definite article for: <b>Femme</b>','la'), ('Guess the correct definite article for: <b>Fleurs</b>','les')
    ],
    'week4': [
        ('Rearrange the jumbled words to form a correct sentence: <br> <b> sommes, Nous, Canada, en, canadiens</b>','Nous sommes canadiens en Canada'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>France, Elle, française, en, est</b>','Elle est française en France'), ('Rearrange the jumbled words to form a correct sentence: <br> <b>est, Il, en, Canada, canadien</b>','Il est canadien en Canada'), ('Rearrange the jumbled words to form a correct sentence: <b>Pakistanais, Ils, l’Inde, en, sont</b>','Ils sont Pakistanais en l’Inde'),
        ('Identify the word or phrase that doesn’t belong in the group: <b>Français, Française, Américain, Espagnol</b>','Française'), ('Identify the word or phrase that doesn’t belong in the group: <b>L’Italie, La Chine, L’Inde, Le Bangladesh"</b>','Le Bangladesh'), ('Identify the word or phrase that doesn’t belong in the group: <b>Je suis, Tu es, Il est, Nous sommes</b>','Nous sommes'), ('Identify the word or phrase that doesn’t belong in the group: <b>Française, Espagnole, Allemande, Indien</b>','Indien'),
        ('Enter the meaning of the word: <b>Vous êtes</b>','you are'), ('Enter the meaning of the word: <b>Ils sont</b>','they are'), ('Enter the meaning of the word: <b>Au</b>','to'), ('Enter the meaning of the word: <b>Nous sommes</b>','we are'), ('Enter the meaning of the word: <b>Américaine</b>','American'),
        ('Guess the correct indefinite article for: <b>Livre</b>','un'), ('Guess the correct indefinite article for: <b>Table</b>','la'), ('Guess the correct definite article for: <b>Restaurant</b>','Le'), ('Guess the correct indefinite article for: <b>Algérienne</b>','une'), ('Guess the correct definite article for: <b>Tunisie</b>','La'), ('Guess the correct definite article for: <b>Châteaux</b>','les'),
        ('Guess the correct indefinite article for: <b>Maison</b>','une'), ('Guess the correct definite article for: <b>France</b>','La'), ('Guess the correct definite article for: <b>Chine</b>','La'), ('Guess the correct indefinite article for: <b>Angleterre</b>','Une')
    ],

}

def select_random_word(week='week1', recent_words_set=[]):
    try:
        recent_words_set = set(recent_words_set)
    except:
        recent_words_set = set('')
    available_words = [wm for wm in grammar_games_dict[week] if wm not in recent_words_set]
    new_word, new_meaning = random.choice(available_words)
    # recent_words.append((new_word, new_meaning))
    return new_word, new_meaning

def initialize(request):
    logging.warning(f"requestinit {request.headers}")
    try:
        week = request.headers.get('week')
    except:
        week = 'week1'
    
    new_word, new_meaning = select_random_word(week)
    
    return {'word':new_word, 'meaning': new_meaning, 'score': 0}

def check_meaning(request, doc, jti):
    logging.warning(f'check meaning request: {request.data}')
    week = json.loads(request.data).get('week')
    input_text = json.loads(request.data).get('input_text')
    try:
        meaning = json.loads(request.data).get('meaning')
    except:
        meaning = ''
    try:
        word = json.loads(request.data).get('word')
    except:
        word = ''
    try:
        consecutive_correct = json.loads(request.data).get('consecutive_correct')
    except: 
        consecutive_correct = 0
    try:
        score = json.loads(request.data).get('score')
    except:
        score = 0

    is_similar=str(check_similarity(word, meaning,input_text))
    logging.warning(f'is similar boolean value: {is_similar}')
    if '1' in is_similar:
    #if input_text.strip().lower() == meaning.strip().lower():
        score += 10
        consecutive_correct += 1
        if consecutive_correct % 3 == 0:
            score += 5

        # db update:
        if (score>int(doc.get().to_dict()[jti]['MM']['high_score'])):
            doc.update({f"{jti}.MM.high_score":score})
       
        doc.update({f"{jti}.MM.correct_answers": firestore.ArrayUnion([{'question': word, 'input': input_text}]), f"{jti}.MM.score":score})
        logging.warning(f"correct check_meaning update: {doc.get().to_dict()}")
    

        return {"result": "correct", "score": score, "consecutive_correct": consecutive_correct}
    elif '0' in is_similar:
        score -= 5
        consecutive_correct = 0

        # db update:
        doc.update({f"{jti}.MM.incorrect_answers": firestore.ArrayUnion([{'question': word, 'input': input_text}]), f"{jti}.MM.score":score})
        logging.warning(f"incorrect check_meaning update: {doc.get().to_dict()}")
        
        return {"result": "incorrect", "score": score, "correct_meaning": meaning, "consecutive_correct": consecutive_correct}

def whisper_transcribe(request, doc, jti):
    """
    Handles transcription of audio using OpenAI's Whisper API.
    """
    try:
        # Ensure the request is multipart and contains the audio file
        print(f'Line 234 from whisper: {request.files}')
        print(f'Line 235 {request.form}')

        # if popup is closed
        if(request.form['cancelled']=='1'):
            print(f"Line 261: close_flag here")
            cc_array = doc.get().to_dict()[jti]['CC']
            # print(f'Line 263 last_message: {cc_array}')
            last_message = cc_array[-1]
            doc.update({f"{jti}.CC": firestore.ArrayRemove([last_message])})
            # print(f'Line 264 last_message: {last_message}')
            last_message['asr']['closed'] = 1

            doc.update({f"{jti}.CC": firestore.ArrayUnion([last_message])})
            
            print("Updated db when popup closed")

            return({'closed':1})
            
        # if user speaks to it
        # Extract the uploaded audio file
        audio_file = request.files['file']
        print(f'Line 263  audio file: {audio_file}')
        
        # Convert the FileStorage object to a file-like object
        file_like = BytesIO(audio_file.read())  # Extract binary content
        print(f'Line 267 file_like {file_like}')
        file_like.name = audio_file.filename  # Add a 'name' attribute

        # Call OpenAI Whisper API
        transcript = openai.Audio.transcribe(
            file=file_like,  # Pass the file-like object
            model="whisper-1",
            language="fr"
        )
        
        transcription = transcript["text"]  # Correctly extract the transcription
        
        # evaluate the uttarance with the real text
        if compare_with_speech(transcription, request.form['correction']):
            print(f'Line 311: {request.form["correction"]}')
            print(f'Line 312: {transcription}')

            return({'match':1})
        else:
            print(f'Line 366 corrected: {request.form["correction"]}')
            print(f'Line 367 transcription: {transcription}')
            cc_array = doc.get().to_dict()[jti]['CC']
            last_message = cc_array[-1]
            doc.update({f"{jti}.CC": firestore.ArrayRemove([last_message])})
            last_message['asr']['wrong_attempts'] += 1

            doc.update({f"{jti}.CC": firestore.ArrayUnion([last_message])})

            print(f"Updated db when wrong speech, jti: {jti}")

            return({'match':0})

    except Exception as e:
        logging.error(f"Error in transcription: {str(e)}")
        return json.dumps({"error": f"Internal server error: {str(e)}"}), 500


def select_unique_words(n=3, week='week1', vocab_recent_words=[]):
    logging.warning('select_unique words week: {week}')
    all_words = set(basic_words[week])
    logging.warning(f'line 289 select unique all_words: {all_words}')
    recent_words_set = set(vocab_recent_words)
    logging.warning(f'line 291 recent_words_set: {recent_words_set}')
    available_words = list(all_words - recent_words_set)
    # available_words = list(all_words)
    
    if len(available_words) < n:
        available_words = list(all_words)
    
    selected_words = random.sample(available_words, n)
    logging.warning(f'selected words: {selected_words}')

    return selected_words

def new_word(request):
    logging.warning(f"new word: {request.data}")
    try:
        week = json.loads(request.data).get('week')
    except:
        week = 'week1'
    try:
        score = json.loads(request.data).get('score')
    except: 
        score = 0
    try: 
        queue = json.loads(request.data).get('queue')
    except:
        queue = []
    new_word, new_meaning = select_random_word(week=week, recent_words_set=queue)
    word = new_word
    meaning = new_meaning
    return {'word': new_word, 'meaning': new_meaning, 'score': score}

def get_vocab(request, doc, jti):
    try:
        week = json.loads(request.data).get('week')
        vocab_recent_words = json.loads(request.data).get('queue')
        logging.warning(f"get_vocab request: {json.loads(request.data)}")
        words = select_unique_words(week=week, vocab_recent_words=vocab_recent_words)

        # db update:
        for word, meaning in words:
            doc.update({f"{jti}.VV.seen_words": firestore.ArrayUnion([word])})
        logging.warning(f"vocab updated in db: {doc.get().to_dict()}")

        return {"words": [{"word": word, "meaning": meaning} for word, meaning in words]}
    except:
        words = select_unique_words()
        for word, meaning in words:
            doc.update({f"{jti}.VV.seen_words": firestore.ArrayUnion([word])})
        logging.warning(f"vocab updated in db: {doc.get().to_dict()}")
        return {"words": [{"word": word, "meaning": meaning} for word, meaning in words]}

paragraphs={'week1':[
            """Le guide: Bonjour, mademoiselle.<br><br>L'étudiante : Bonjour, monsieur.<br><br>
                Le guide: Comment vous appelez-vous?<br><br>
                L'étudiante: Michelle Dubois.<br><br>
                Le guide: Ah, je suis aussi Michel! Enchanté, Michelle. Je suis Michel Bertrand.<br><br>
                L'étudiante: Oh, quelle coïncidence! Enchantée, Michel.""",
            """Bonjour, je m'appelle Audrey, j'ai 19 ans. Je suis américaine et indienne. J'apprends le français pour pouvoir étudier la médecine en France. Où étudiez-vous le français?"""
        ],
        
        'week2':[
            """La touriste: Je m'appelle Saroj.<br><br>
                La guide: Comment?<br><br>
                La touriste: Saroj Kaul.<br><br>
                La guide: Vous pouvez épeler, s'il vous plaît.<br><br>
                La touriste: S-A-R-O-J K-A-U-L.<br><br>
                La guide: Merci.<br><br>""",
            """Alice: Bonjour, je m'appelle Alice. Je suis américaine et j'habite à New York. Vous êtes le professeur de français?<br><br>
                Monsieur Dupont: Oui, bonjour Alice. Je m'appelle Monsieur Dupont. Je suis français et j'habite à Paris. Comment puis-je vous aider aujourd'hui?<br><br>
                Alice: Je voudrais pratiquer le français. Pouvez-vous répéter la leçon lentement, s'il vous plaît?<br><br>
                Monsieur Dupont: Bien sûr. Écoutez attentivement et parlez plus fort si vous avez des questions. Lisez ce texte pour améliorer votre compréhension.<br><br>
                Alice: Merci, Monsieur Dupont. Je suis très content de commencer les cours.<br><br>
                Monsieur Dupont: De rien, Alice. Je suis heureux de vous aider."""
        ],

        'week3':[
            """Bonjour! Je m'appelle Céline. Écoutez, s'il vous plaît. Répétez après moi. Parlez lentement. Lisez cette phrase. Épeler votre nom, s'il vous plaît. Parlez plus fort.""",
            """Le chat est noir. La maison est grande. L'oiseau chante. Un chien court. Une fille lit. Des livres sont sur la table. L'homme mange une pomme.""",
            """Je suis étudiant et tu es mon professeur. Il est français et elle est américaine. Nous sommes dans une classe de langue. Vous êtes tous attentifs. Ils sont amateurs, mais elles sont débutantes en français."""
        ],
        
        'week4': [
            """La serveuse: Et voici un café.<br><br>
                Luigi: Merci. Vous êtes belge?<br><br>
                La serveuse: Non, je suis allemande.<br><br>
                Luigi: Vous parlez bien français.<br><br>
                La serveuse: Merci. Et vous, vous êtes français?<br><br>
                Luigi: Non, italien.""",
            """Je m’appelle Jessica. Je suis une fille, je suis française et j’ai treize ans. Je vais à l’école à Nice. J’ai deux frères. Le premier s’appelle Thomas, il a quatorze ans. Le second s’appelle Yann et il a neuf ans. Mon papa est italien et il est fleuriste. Ma mère est allemande et est avocate. Mes frères et moi parlons français, italien et allemand à la maison. Nous avons une grande maison avec un chien et deux chats.""",
            """Il s'appelle Slievanie Mansourt. Il a 20 ans et il est algérien. Il habite en Algérie et il parle arabe. Rani est une amie indienne. Elle a 22 ans et elle parle hindi. Il y a aussi Ahmed, un jeune homme pakistanais de 24 ans. Il parle ourdou. Enfin, il y a Sarah, une étudiante tunisienne. Elle a 21 ans et elle vit en Tunisie où elle parle arabe et français."""
        ]
        }

def get_para(request):
    try:
        week = json.loads(request.data).get('week')
        logging.warning(f"line 308 week name: {week}")
        p=random.choice(paragraphs[week])
        logging.warning(f"line 310 paragraph: {p}")
        return {'paragraph':p}
    except:
        return {'paragraph':paragraphs['week1'][0]}

def save_privacy(request, doc):
    try:
        print(f"Line 494 Request: {json.loads(request.data)}")
        # if privacy in data:
        if json.loads(request.data).get('privacy') == 1:
            doc.update({'privacy':1})
        else:
            doc.update({'privacy':0})
        return {"Okay":1}
    except:
        print(f"Line 502: {request.data}")
        return {"No request only":0}

def download_firestore_collection():
    try:
        collection_name = os.getenv("COLLECTION_NAME")
        collection_ref = db.collection(collection_name)
        docs = collection_ref.stream()

        # Gather all documents data
        all_data = {}
        for doc in docs:
            all_data[doc.id] = doc.to_dict()

        if not all_data:
            return Response(json.dumps({"error": "No data found"}), status=404, mimetype='application/json', headers=headers)

        # Prepare JSON data
        json_data = json.dumps(all_data, indent=4)
        json_filename = f"{collection_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        # Create in-memory file
        file_buffer = io.BytesIO(json_data.encode('utf-8'))

        # Send JSON file as attachment
        return send_file(
            file_buffer,
            as_attachment=True,
            download_name=json_filename,
            mimetype='application/json'
        )

    except Exception as e:
        return Response(json.dumps({"error": str(e)}), status=500, mimetype='application/json', headers=headers)


@functions_framework.http
def home(request):
    if request.method == 'OPTIONS':
        return Response(status=204, headers=headers)

    token = request.headers.get('Authorization')
    if not token:
        return Response(json.dumps({"error": "Authentication token is missing."}), status=400, mimetype='application/json', headers=headers)

    if token.startswith("Bearer "):
        token = token[7:]

    try:
        id_info = id_token.verify_oauth2_token(token, requests.Request(), GOOGLE_OAUTH2_CLIENT_ID)
    except Exception:
        return Response(json.dumps({"error": "The provided token is invalid."}), status=401, mimetype='application/json', headers=headers)

    email = id_info.get("email")
    if not email:
        return Response(json.dumps({"error": "Email address is missing in the token."}), status=401, mimetype='application/json', headers=headers)

    collection = db.collection(os.getenv("COLLECTION_NAME"))
    # logging.warning(f"id_info: {id_info}")

    username = email.replace('@flame.edu.in','')
    jti = id_info.get("jti")
    documents = collection.document(username)

    # # uncomment to allow access to only specific users with the flame email id
    # logging.warning(f"username: {username}")
    # # if not documents:
    # #     return Response(json.dumps({"error": "You are not authorised."}), status=401, mimetype='application/json', headers=headers)
    # doc = documents.get()
    # if not doc.exists:
    #     data = {'name': id_info.get('name'), jti:{'timestamp':[datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),datetime.now().strftime("%Y-%m-%d_%H-%M-%S")],'CC':[{'user_response':'', 'assistant_response':{'correction':'', 'response':'', 'translation':''}, 'week':''}], 'MM':{'score':0, 'high_score':0, 'correct_answers':[], 'incorrect_answers':[]}, 'VV':{'seen_words':[]}}}
    #     documents.set(data)
    #     logging.warning(f"documents set for first time: {doc.to_dict()}")
    
    # # else if documents exists:
    # documents.update({jti:{'timestamp':[datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),datetime.now().strftime("%Y-%m-%d_%H-%M-%S")],'CC':[{'user_response':'', 'assistant_response':{'correction':'', 'response':'', 'translation':''}, 'week':''}], 'MM':{'score':0, 'high_score':0, 'correct_answers':[], 'incorrect_answers':[]}, 'VV':{'seen_words':[]}}})
    # logging.warning(f"documents already there: {documents.get().to_dict()}")
    


    if request.method == 'GET':
        if request.path == "/initialize" :
            logging.warning(request.data)
            update_timestamps(documents, jti)
            response = initialize(request)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)

        elif request.path == "/vocab":
            update_timestamps(documents, jti)
            response = get_vocab()
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)

    elif request.method == "POST":
        if request.path == "/login":
            response = login(id_info)
            return Response(json.dumps(response), status=200, mimetype='application/json', headers=headers)
        elif request.path == "/chat":
            update_timestamps(documents, jti)
            response = chat(request, documents, jti)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/check_meaning":
            update_timestamps(documents, jti)
            response = check_meaning(request, documents, jti)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/vocab":
            update_timestamps(documents, jti)
            response = get_vocab(request, documents, jti)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/new_word":
            update_timestamps(documents, jti)
            response = new_word(request)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/para":
            logging.warning(json.loads(request.data))
            update_timestamps(documents, jti)
            response = get_para(request)
            logging.warning(response)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/whisper":
            update_timestamps(documents, jti)
            response = whisper_transcribe(request, documents, jti)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
        elif request.path == "/privacy":
            update_timestamps(documents, jti)
            response = save_privacy(request, documents)
            return Response(json.dumps(response), status=200 if "error" not in response else 500, mimetype='application/json', headers=headers)
    return Response(json.dumps({"error": "Not Found"}), status=404, mimetype='application/json', headers=headers)
