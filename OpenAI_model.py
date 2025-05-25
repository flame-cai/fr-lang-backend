from datetime import datetime
import openai
from utils import *
import json
import os
import logging


class OpenAIBot():
    def __init__(self, lang, base, user_id='testman'):

        # #create file to save msg history
        # self.filedir = f'messages/{user_id}'
        # if not os.path.exists(self.filedir):
        #     os.mkdir(self.filedir)
        #     os.mkdir(f'{self.filedir}/cc')
        #     os.mkdir(f'{self.filedir}/mm')
        # current_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        # self.filename = (f"./{self.filedir}/cc/messages_{current_time}.txt")
        # with open(self.filename, 'w') as f:
        #     pass
        # print(f'file {self.filename} initialised')

        openai.api_key = os.getenv("OPENAI_API_KEY")
        # Define the system prompt
        # self.system_prompt = f"Have a conversation and teach the user {lang} based on the metrics given below and switch to {base} when the user needs help understanding. \
        #     'Beginner': use as basic and simple vocabulary and sentence structures as possible. Must avoid idioms, slang, and complex grammatical constructs. \
        #     'Intermediate': use a wider range of vocabulary and a variety of sentence structures. You can include some idioms and colloquial expressions, \
        #     but avoid highly technical language or complex literary expressions. \
        #     'Advanced': use sophisticated vocabulary, complex sentence structures, idioms, colloquial expressions, and technical language where appropriate."
        self.lang = lang
        self.base = base
        self.user_id = user_id
        self.verbosity = 10
        self.max_words = 0
        self.avg_words = 0

        self.MODEL = "gpt-4o-2024-08-06"
        # self.system_prompt=(f"roleplay as a barista in a basic A1 level {self.lang} teaching class to have a free flowing conversation with the user while teaching them in the process. Strictly do not translate anything in {self.base}. Teach them more words in {self.lang} appropriate for the scenario but do not correct the user's mistakes")
        self.system_prompt = ('')
        self.conversation_history = [{
            "role": "system",
            "content": self.system_prompt
        }]

    def change_level(self,assistant_response,chat_history):
        message=f'{{"debug": "response changed"}}'
        # with open(self.filename, 'a') as f:
        #     f.write(message + '\n')

        consolidated_response = ''
        for i in chat_history:
          consolidated_response += ':'.join(list(i.values()))
          consolidated_response += '\n'
        # print(end_string)
        consolidated_response += f'assistant:{assistant_response}'

        num_sent = 1 if (self.avg_words <= 5) else 2 if (self.avg_words <= 10) else 3
        num_words = self.max_words+5

        system_message = {
        "role": "system",
        "content": (f'The user message provided contains the transcript in chronological order for a conversation between a user and a bot that is meant to assist the user in learning CEFR level A1 {self.lang}. A feedback mechanism has determined that the last message from the bot is too complex for the user level. Simplify the last bot message so that the message contains no more than {num_sent} {self.lang} sentences with at most {num_words} {self.lang} words per sentence. Return only the corrected bot response strictly without any additional text')
        }

        user_message = {
            "role": "user",
            "content": consolidated_response
        }

        conv = [system_message,user_message]
        # while True:
        response = openai.ChatCompletion.create(
              model="gpt-4o-2024-08-06",  # model="gpt-3.5-turbo-0125", "gpt-4-1106-preview" "gpt-4-0125-preview"
              messages=conv,
              temperature=0.0,
              max_tokens=1000, #was 3000
              top_p=1,
              frequency_penalty=0,
              presence_penalty=0,
          )
        
        
            # Append the AI's response to the conversation
        AI_response = response.choices[0].message['content']
        # if WSTF(AI_response)< self.w_score+2:
        return AI_response

    def add_message(self, role, content):
        # Adds a message to the conversation history.
        self.conversation_history.append({"role": role, "content": content})
        role=self.conversation_history[-1]['role']
        message=(self.conversation_history[-1]['content']).replace('\n','')
        # with open(self.filename, 'a') as f:
        #     f.write(f'{{"{role}" : "{message}"}}\n')
        pass

    def correct_user(self,prompt):
        system_message = {
        "role": "system",
        "content": (f"correct the user's grammar and syntax when they say something in {self.lang} and explain it in {self.base} in 1 or 2 sentences. Say Only: 'Correct' if everything is right.")
        }

        user_message = {
            "role": "user",
            "content": prompt
        }
        
        conv = [system_message,user_message]
        # while True:
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
        # with open(self.filename,'a') as f:
        #     f.write(f'{{"correction": "{AI_response}"}}\n')
        return (AI_response)

    def full_translation(self,prompt):
        system_message = {
        "role": "system",
        "content": (f"fully translate the {self.lang} into {self.base} and put it in brackets. Only give the translation and do not repeat the {self.lang} part. Never translate {self.base} to {self.lang}, instead of translating, return those words as is.")
        }

        user_message = {
            "role": "user",
            "content": prompt
        }
        
        conv = [system_message,user_message]
        # while True:
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
        # with open(self.filename, 'a') as f:
        #     f.write(f'{{"translation": "{AI_response}"}}\n')
        return (AI_response)

    def language_breakdown(self,response):
        system_message = {
        "role": "system",
        #"content": (f"Break down the given {self.lang} sentence(s) into phrases or words that can be easily translated in english, have the translation next to the german word/phrase in brackets and keep the sentence structure the same")
        "content": (f"Break down the given {self.lang} sentence(s) into phrases or words that are translated in {self.base}, keep the sentence structure and punctuations the same and return it as a list of tuples in the form (\"word in {self.lang}\",\"meaning in {self.base}\") with all the punctuations attached to the word before them.`Always return only a list of tuples and no extra text.` Do not translate {self.base} words to {self.lang}, return them as {self.base} words.")
        }

        AI_message = {
            "role": "user",
            "content": response
        }
        
        conv = [system_message,AI_message]
        # while True:
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

        # Parse the response into a dictionary
        # translation_dict = {}
        # words = AI_response.split("")
        # for word in words:
        #     if '(' in word and ')' in word:
        #         german_word, translation = word.split('(')
        #         translation = translation.rstrip(')')
        #         translation_dict[german_word] = translation
        #translation_dict = json.loads(AI_response)
        #print(AI_response)

        # print(f'ai response before: {AI_response}')
        
        # translation_dict = json.loads(AI_response.replace(')',']').replace('(','['))
        # print(f'translationL {translation_dict}')
        # print(f'new l {merge_punctuations(translation_dict)}')

        # AI_response = f"{merge_punctuations(translation_dict)}"
        # print(f'ai response after: {AI_response}')

        # with open(self.filename, 'a') as f:
        #     f.write(f'{{"break_down": "{AI_response}"}}')
        return AI_response

    def generate_response(self, prompt):
        try:
            self.response = openai.ChatCompletion.create(
            model=self.MODEL,  # model="gpt-3.5-turbo-0125", "gpt-4-1106-preview" "gpt-4-0125-preview"
            messages=self.conversation_history,
            temperature=0,
            max_tokens=3000, #was 3000
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
            )
            # print(self.response['choices'][0]['message']['content'])
            # score user's message
            if len(self.conversation_history)>4:
                self.verbosity = max(len(tokenize_text(self.conversation_history[-5]['content'])),len(tokenize_text(self.conversation_history[-3]['content'])),len(tokenize_text(self.conversation_history[-1]['content'])))
            # print(self.verbosity)
            usermsg_verbosity = len(tokenize_text(self.conversation_history[-1]['content']))
            # print(self.verbosity)
            
            # find highest score
            if self.verbosity < usermsg_verbosity:
              self.verbosity = usermsg_verbosity
            
            # print(f'max_verbosity={self.verbosity}')
            # with open(self.filename, 'a') as f:
            #     f.write(f'{{"max_verbosity" : {self.verbosity}}}\n')
            # Extract the response
            assistant_response = self.response['choices'][0]['message']['content'].strip()
            logging.warning("Asssitant Response: %s", assistant_response)
            logging.warning("Prompt: %s", prompt)

            lang_prompt=extract(prompt, self.lang)
            # print(f'lang_prompt 230 {lang_prompt}')
            lang_AI_response=extract(assistant_response, self.lang)
            # print(f'{tokenize_sentences(lang_prompt)}')
            # print(f'lang_ai_resp {lang_AI_response}')
            AI_verbosity=len(tokenize_text(lang_AI_response))

            if(len(lang_prompt)==0):
                self.add_message("assistant", assistant_response)
                logging.warning("Passed over Line 241 openAI_model")
                logging.warning(f"Passed over Line 242 openAI_model {assistant_response}")
                # Return the response
                return assistant_response

            logging.warning("Passed over Line 244 openAI_model")
            # user_max_words=max([len(tokenize_text(i)) for i in (tokenize_sentences(lang_prompt))])
            # user_average_word=len(tokenize_text(lang_prompt))/len(tokenize_sentences(lang_prompt))
            # print(f'user_max_words {user_max_words}')
            # print(f'user_average_word {user_average_word}')




            # if self.max_words<user_max_words:
            #   self.max_words=user_max_words

            # if self.avg_words<user_average_word:
            #   self.avg_words=user_average_word

            
            # print(f'AI verbosity {AI_verbosity}')
            if AI_verbosity>(self.verbosity+5):
                # print original AI message
                # print(assistant_response)
                logging.warning("Passed over Line 264 openAI_model")
                assistant_response = self.change_level(assistant_response,self.conversation_history[-5:])

            #break the language down by words or phrases
            #assistant_response=self.language_breakdown(assistant_response)

            #correct user
            #correction=self.correct_user(prompt)
            #assistant_response=correction + " \n " + assistant_response
            #print('158',assistant_response)
            # Add assistant response to conversation history

            self.add_message("assistant", assistant_response)
            logging.warning(f"Passed over Line 279 openAI_model {assistant_response}")
            # Return the response
            return assistant_response
        except Exception as e:
            print(f"Error generating response: {e}")