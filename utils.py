import nltk
import openai
import os
# from polyglot.detect import Detector
from nltk.tokenize import word_tokenize, sent_tokenize
# from langdetect import detect, DetectorFactory
# from langdetect.lang_detect_exception import LangDetectException
import re

# DetectorFactory.seed = 0
nltk.download('punkt')

def tokenize_text(text):
    words = word_tokenize(text)
    words = [word for word in words if word.isalpha()]
    return words

def tokenize_sentences(text):
    sentences = sent_tokenize(text)
    return sentences

MODEL = "gpt-4o-mini-2024-07-18" # was gpt-4-0125-preview
openai_key = os.getenv("OPENAI_API_KEY")

def extract(text, lang):
    openai.api_key = openai_key

    system_message = {
    "role": "system",
    "content": (f'Given a mixed English-{lang} sentence, remove the English parts of the sentence, without adding any new text and keeping the punctuations.')
    }

    user_message = {
        "role": "user",
        "content": text
    }

    conv = [system_message,user_message]
    while True:
      response = openai.ChatCompletion.create(
          model=MODEL,  # model="gpt-3.5-turbo-0125", "gpt-4-1106-preview" "gpt-4-0125-preview"
          messages=conv,
          temperature=0.0,
          max_tokens=1000, #was 3000
          top_p=1,
          frequency_penalty=0,
          presence_penalty=0,
      )
        # Append the AI's response to the conversation
      return response.choices[0].message['content']
    
def check_similarity(question, meaning, guessed_meaning):
    question = question.replace('<b>','').replace('</b>','')
    system_message = {
    "role": "system",
    "content": (f"Check the input question and return 1 if guessed_answer is the correct answer to the input question. Return 1 even if there is a minor spelling mistake in French or a capitalization error, but return 0 if guessed_answer is not correct anser to the question, refer to correct_reference for the correct answer. ONLY RETURN 1 OR 0, NOTHING ELSE.")
    }

    user_message = {
        "role": "user",
        "content": f"question: {question}, correct_reference: {meaning}, guessed_answer: {guessed_meaning}"
    }
    
    conv = [system_message,user_message]
    response = openai.ChatCompletion.create(
            model="gpt-4o-mini-2024-07-18",  # model="gpt-3.5-turbo-0125", "gpt-4-1106-preview" "gpt-4-0125-preview"
            messages=conv,
            temperature=0.0,
            max_tokens=1000, #was 3000
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )
    AI_response = response.choices[0].message['content']
    return (AI_response)    

def syllables(word):
    count = 0
    vowels = 'aeiouy'
    word = word.lower()
    if word[0] in vowels:
        count +=1
    for index in range(1,len(word)):
        if word[index] in vowels and word[index-1] not in vowels:
            count +=1
    if word.endswith('e'):
        count -= 1
    if word.endswith('le'):
        count += 1
    if count == 0:
        count += 1
    c=[]
    c.append(count)
    return c

nltk.download('cmudict')
from nltk.corpus import cmudict
d = cmudict.dict()

def nsyl(word):
    try:
        return [len(list(y for y in x if y[-1].isdigit())) for x in d[word.lower()]]
    except KeyError:
      #if word not found in cmudict
      return syllables(word)
    
def MS(corpus):
    words = tokenize_text(corpus)
    total_words = len(words)
    words_with_more_than_3_syllables = sum(1 for x in words if int(nsyl(x)[0]) > 3)
    percentage = (words_with_more_than_3_syllables / total_words) * 100
    return percentage

def SL(corpus):
    sentences = tokenize_sentences(corpus)
    total_sentences = len(sentences)
    total_words = sum(len(tokenize_text(sentence)) for sentence in sentences)
    mean_words_per_sentence = total_words / total_sentences if total_sentences > 0 else 0
    return mean_words_per_sentence

def IW(corpus):
  l=tokenize_text(corpus)
  mt6=sum(1 for x in l if len(x)>6)
  percentage=mt6/len(l) * 100
  return percentage

def ES(corpus):
    words = tokenize_text(corpus)
    total_words = len(words)
    words_with_more_than_1_syllables = sum(1 for x in words if int(nsyl(x)[0]) == 1)
    percentage = (words_with_more_than_1_syllables / total_words) * 100
    return percentage

def WSTF(txt):
  print((0.1935 * MS(txt)) + (0.1672 * SL(txt)) + (0.1297* IW(txt)) - (0.0327 * ES(txt)) - 0.875)
  return((0.1935 * MS(txt)) + (0.1672 * SL(txt)) + (0.1297* IW(txt)) - (0.0327 * ES(txt)) - 0.875)

def process_correction_string(correction_string):
    # Load the corpus (list of words from the filtered file)
    corpus_file = "french_corpus.txt"
    with open(corpus_file, "r", encoding="utf-8") as file:
        corpus = {line.strip().lower() for line in file}  # Ensure lowercase for corpus
    
    # Remove everything including and after the word "Explanation"
    correction_string = re.split(r'\bExplanation\b', correction_string, maxsplit=1)[0]

    # Extract the text inside quotes
    # Extract the text inside quotes
    quoted_text = correction_string.replace('Corrected','').replace(':','').replace('"','').replace('-',' ')
    print(f'UTILS quoted_text: {quoted_text}')

    # Convert to lowercase and remove punctuation
    cleaned_text = re.sub(r'[^\w\s]', '', quoted_text.lower())

    # Split into words and filter those in corpus
    cleaned_words = cleaned_text.split()
    filtered_words = [word for word in cleaned_words if word in corpus]

    # Get original words while preserving case
    original_words = quoted_text.split()
    final_sentence = []
    
    # Keep track of which filtered words we've matched
    filtered_index = 0
    
    # Process each original word
    for original_word in original_words:
        cleaned_original = re.sub(r'[^\w\s]', '', original_word.lower())
        # Check if this word is in our filtered list
        if filtered_index < len(filtered_words) and cleaned_original == filtered_words[filtered_index]:
            final_sentence.append(original_word)
            filtered_index += 1

    return " ".join(final_sentence)

# Function to compare the processed string with speech text
def compare_with_speech(processed_text, speech_text):
    processed_text = re.sub(r'[^\w\s]', '', processed_text.lower().replace("-",' ')).rstrip()
    speech_text = re.sub(r'[^\w\s]', '', speech_text.lower().replace("-",' ')).rstrip()
    print(f'correct: {processed_text}')
    print(f'asr: {speech_text}')
    return processed_text == speech_text
