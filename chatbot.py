### pip3 install nltk
import nltk
from nltk.stem.lancaster import LancasterStemmer
stemmer = LancasterStemmer()

import numpy
import tensorflow as tf
from tensorflow.keras import layers, models

import random
import json
import pickle

with open("chatbot_intents.json") as file:
    data = json.load(file)

with open("chatbot_data.pickle", "rb") as f:
    words, labels, training, output = pickle.load(f)

# Load Model
model = models.load_model('models/chatbot_dnn.h5')

def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1
            
    return numpy.array(bag)


def chat():
    print("Start talking with the bot (type quit to stop)!")
    while True:
        inp = input("You: ")
        if inp.lower() == "quit":
            break

        results = model.predict(numpy.array([bag_of_words(inp, words)]))
        print('confidence: '+str(numpy.max(results)*100))
        results_index = numpy.argmax(results)
        tag = labels[results_index]

        for tg in data["intents"]:
            if tg['tag'] == tag:
                responses = tg['responses']

        print(random.choice(responses))

chat()
