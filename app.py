from tensorflow.keras.preprocessing.sequence import pad_sequences
import pickle
import numpy as np
import tensorflow as tf
import json
import os
from datetime import datetime
from flask import Flask, render_template, request, redirect, session
import random
from nltk.corpus import stopwords
import string
import nltk
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
import spacy
import re
from spellchecker import SpellChecker
from nltk.tokenize import word_tokenize



nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set a secret key for session management

# Load the tokenizer
with open('tokenizer.pkl', 'rb') as f:
    tokenizer = pickle.load(f)

threshold = 0.5

# Load the emotion trained model
model = tf.keras.models.load_model('emotion_model_trained.h5')

# Load stop words
stop_words = set(stopwords.words('english'))

# Initialize lemmatizer and stemmer
lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

# Initialize spaCy for lemmatization
nlp = spacy.load('en_core_web_sm')

# Initialize spell checker
spell = SpellChecker()

# Preprocess the text by removing stop words, punctuation, handling emojis and emoticons, lemmatization, handling repeated characters, and spell correction
def preprocess_text(text):
    # Replace comma, inverted commas, "the", "and", full stop, and exclamation mark
    text = text.replace(',', '')
    text = text.replace('\'', '')
    text = text.replace('\"', '')
    text = text.replace('the ', '')
    text = text.replace('and ', '')
    text = text.replace('. ', '')
    text = text.replace('!', '')
    text = text.replace("can't", "cannot")
    text = text.replace("don't", "do not")
    text = text.replace("I'm", "I am")
    text = text.replace("it's", "it is")
    text = text.replace("I've", "I have")
    text = text.replace("isn't", "is not")
    text = text.replace("won't", "will not")
    text = text.replace("doesn't", "does not")
    text = text.replace("they're", "they are")
    text = text.replace("haven't", "have not")
    text = text.replace("shouldn't", "should not")
    text = text.replace("wouldn't", "would not")
    text = text.replace("wasn't", "was not")
    text = text.replace("weren't", "were not")
    text = text.replace("hasn't", "has not")
    text = text.replace("couldn't", "could not")
    text = text.replace("aren't", "are not")
    text = text.replace("didn't", "did not")
    text = text.replace("doesn't", "does not")
    text = text.replace("mustn't", "must not")
    text = text.replace("shan't", "shall not")
    text = text.replace("mightn't", "might not")
    text = text.replace("she's", "she is")
    text = text.replace("he's", "he is")
    text = text.replace("we're", "we are")
    text = text.replace("you're", "you are")
    text = text.replace("let's", "let us")
    text = text.replace("that's", "that is")


    # Convert to lowercase
    text = text.lower()

    # Tokenize the text
    sequence = word_tokenize(text)

    # Lemmatization or stemming
    lemmatized_sequence = [lemmatizer.lemmatize(word) for word in sequence]

    # Handling repeated characters
    processed_sequence = []
    for word in lemmatized_sequence:
        processed_sequence.append(re.sub(r'(.)\1+', r'\1\1', word))

    # Spell correction
    corrected_sequence = [spell.correction(word) for word in processed_sequence if isinstance(word, str)]

    # Removing special characters
    special_chars = string.punctuation
    processed_sequence = [word for word in corrected_sequence if word and word not in special_chars]

    # Convert words to indices using tokenizer
    indexed_sequence = tokenizer.texts_to_sequences([processed_sequence])[0]

    # Pad the sequence
    padded_sequence = pad_sequences([indexed_sequence], truncating='post', maxlen=50, padding='post')

    return padded_sequence












def predict_emotion(text):
    # Preprocess the text
    processed_text = preprocess_text(text)

    # Predict the emotion probabilities
    predicted_probs = model.predict(processed_text)[0]

    # Get the indices of the top 3 probabilities in descending order
    top_indices = np.argsort(predicted_probs)[::-1][:3]

    # Map the indices to the corresponding emotions and probabilities
    emotions = ['anger', 'fear', 'sadness', 'surprise', 'joy', 'love']
    top_emotions = [emotions[idx] for idx in top_indices]
    top_probabilities = [float(predicted_probs[idx]) for idx in top_indices]  # Convert to float

    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Get the current timestamp

    return top_emotions, top_probabilities, timestamp  # Return emotions, probabilities, and timestamp

random_string = ""

def save_history(history):
    with open('history.json', 'w') as f:
        json.dump(history, f)

def load_history():
    if not os.path.exists('history.json'):
        with open('history.json', 'w') as f:
            f.write("[]")  # Write an empty list to the file
        return []  # Return an empty list as the history

    try:
        with open('history.json', 'r') as f:
            history = json.load(f)
    except:
        history = []
    return history

def predict_inferred_emotions(emotions, probabilities, threshold):
    inferred_emotions = []

    # Define the rules for inferring emotions based on the given emotions
    rules = [
    (('joy', 'love'), 'bliss'),
    (('surprise', 'love'), 'affection'),
    (('surprise', 'joy'), 'elation'),
    (('sadness', 'joy'), 'nostalgia'),
    (('sadness', 'love'), 'melancholy'),
    (('fear', 'joy'), 'excitement'),
    (('fear', 'love'), 'longing'),
    (('anger', 'joy'), 'exasperation'),
    (('anger', 'love'), 'passion'),
    (('sadness', 'surprise', 'love'), 'bittersweet'),
    (('sadness', 'surprise'), 'disappointment'),
    (('anger', 'surprise'), 'outrage'),
    (('fear', 'surprise'), 'anxiety'),
    (('surprise',), 'surprise'),
    (('anger', 'sadness'), 'resentment'),
    (('anger', 'fear', 'sadness'), 'resigned'),
    (('anger', 'fear'), 'frustration'),
    (('sadness', 'fear'), 'despair'),
    (('fear',), 'fear'),
    (('sadness',), 'sadness'),
    (('anger',), 'anger'),
    (('joy',), 'joy'),
    (('love',), 'love'),
    (('joy', 'surprise', 'love'), 'delight'),
    (('anger', 'surprise', 'joy'), 'indignation'),
    (('fear', 'sadness', 'joy'), 'admiration'),
    (('fear', 'sadness', 'love'), 'sorrow'),
    (('anger', 'fear', 'joy'), 'outrage'),
    (('anger', 'fear', 'love'), 'rage'),
    (('surprise', 'sadness', 'fear'), 'awe'),
    (('surprise', 'sadness', 'love'), 'amazement'),
    (('surprise', 'sadness', 'joy'), 'amusement'),
    (('fear', 'surprise', 'love'), 'trepidation'),
    (('anger', 'sadness', 'love'), 'heartache'),
    (('anger', 'surprise', 'sadness'), 'fury'),
    (('anger', 'surprise', 'fear'), 'hostility'),
    (('sadness', 'fear', 'love'), 'grief'),
    (('sadness', 'surprise', 'joy'), 'regret'),
    (('sadness', 'surprise', 'fear'), 'pity'),
    (('sadness', 'joy', 'love'), 'yearning'),
    (('anger', 'joy', 'love'), 'zeal')
    ]


    filtered_emotions = []

    # Filter emotions based on probability threshold
    for i in range(len(emotions)):
        if probabilities[i] >= threshold:
            filtered_emotions.append(emotions[i])

    # Check if any of the defined rules match the filtered emotions
    for rule_emotions, inferred_emotion in rules:
        if all(emotion in filtered_emotions for emotion in rule_emotions):
            inferred_emotions.append(inferred_emotion)

    # Remove atomic emotions from inferred emotions if its size is greater than 3
    if len(inferred_emotions) > 3:
        inferred_emotions = [emotion for emotion in inferred_emotions if emotion not in ('anger', 'fear', 'sadness', 'surprise', 'joy', 'love')]
    print("THRESHOLD:", threshold)
    print("FILTERED EMOTION:", filtered_emotions)
    print("INFERRED EMOTION:", inferred_emotions)
    return inferred_emotions

def get_random_string():
    with open('test_text.txt', 'r') as file:
        lines = file.readlines()
        random_string = random.choice(lines).strip()
        return random_string


history = load_history()


@app.route('/', methods=['GET', 'POST'])
def index():
    inferred_emotions = []

    if request.method == 'POST':
        text = request.form['text']
        emotions, probabilities, timestamp = predict_emotion(text)
        inferred_emotions = predict_inferred_emotions(emotions, probabilities, threshold)
        entry = {
            'text': text,
            'emotions': emotions,
            'probabilities': probabilities,
            'inferred_emotions': inferred_emotions,
            'timestamp': timestamp
        }
        history.insert(0, entry)
        save_history(history)
        return redirect('/')
        
    
    return render_template('index.html', history=history, inferred_emotions=inferred_emotions, threshold=session.get('threshold', 0.5), random_string=random_string)

@app.route('/clear', methods=['POST'])
def clear_history():
    history.clear()
    save_history(history)
    return redirect('/')

@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    global threshold  # Declare the threshold variable as global
    threshold = float(request.form['threshold'])
    session['threshold'] = threshold  # Update the threshold value in the session
    return redirect('/')


@app.route('/random', methods=['POST'])
def random_text():
    global random_string
    random_string = get_random_string()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)

