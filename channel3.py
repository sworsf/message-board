import random
from flask import Flask, request, jsonify
import json
import requests
import re


# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '33445566'
CHANNEL_NAME = "Eggliza"
CHANNEL_ENDPOINT = "http://localhost:5003"
CHANNEL_FILE = 'messages.json'

RESPONSES = [
    (r'hi|hello', ['Hello!', 'Hi there! How can I help you today?']),
    (r'how are you', ['I\'m just a bot, but I\'m doing well, thank you!']),
    (r'.*', ['Interesting, tell me more.', 'Why do you say that?', 'How does that make you feel?'])
]

@app.cli.command('register')
def register_command():
    """Register this channel with the hub."""
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
                                 "name": CHANNEL_NAME,
                                 "endpoint": CHANNEL_ENDPOINT,
                                 "authkey": CHANNEL_AUTHKEY
                             }))
    if response.status_code != 200:
        print("Error registering channel:", response.status_code)
    else:
        print("Channel registered successfully.")

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200
def eliza_response(message):
    """Generate whimsical, egg-themed responses based on keywords in the user's message."""
    # Categorized egg puns, facts, and jokes based on potential keywords
    EGG_CONTENT = {
        'why': [
            "Why did the chicken go to the séance? To talk to the other side!",
            "Why did the egg regret being in an omelette? It wasn't all it was cracked up to be.",
            "Why did the egg go to school? To get egg-ucated!",
            "Why don't eggs tell jokes? They'd crack each other up."
        ],
        'how': [
            "How do eggs get around? On a s-egg-way!",
            "How does an egg leave its house? Through the eggs-it!"
        ],
        'what': [
            "What's an egg's least favorite day of the week? Fry-day!",
            "What do you call a mischievous egg? A practical yolker!",
            "What did the egg say to the clown? You crack me up!"
        ],
        'hello': [
            "Hello! If you were an egg, how would you like to be cooked?",
            "Hi there! Ready to egg-sperience some egg-citing puns?"
        ],
        'name': [
            "They call me the Eggcelent Chatbot. Ready to crack some jokes?",
            "I'm just a humble egg in this digital world, looking to whisk up some fun."
        ],
        'feel': [
            "Feeling eggstraordinary! And you?",
            "Just egg-static to be chatting with you!"
        ],
        'joke': [
            "Why did the egg get thrown out of class? For telling yolk-y jokes!",
            "How do comedians like their eggs? Funny side up!"
        ],
        'food': [
            "If food is the question, then eggs are definitely the answer!",
            "Talking about food, did you know eggs are egg-ceptionally versatile?"
        ],
        'default': [
            "Eggs are fantastic for a fitness diet. Try egg-cersizing!",
            "I was going to tell you an egg joke, but it's not all it's cracked up to be.",
            "Did you hear about the hen who could count her own eggs? She was a mathemachicken!",
            "If you walk on eggs, you will likely scramble.",
            "Did you hear about the egg who got into a heated argument? It got beaten.",
            "Sometimes I feel like an egg: I'm pretty hard-boiled on the outside but still a bit runny in the middle."
        ]
    }

    # Find the first keyword in the message that matches a category, if any
    for keyword in EGG_CONTENT.keys():
        if re.search(r'\b' + keyword + r'\b', message, re.IGNORECASE):
            # Select a random response from the matching category
            return random.choice(EGG_CONTENT[keyword])

    # If no keywords match, select a random response from the 'default' category
    return random.choice(EGG_CONTENT['default'])


@app.route('/', methods=['GET', 'POST'])
def home_page():
    """Endpoint for getting messages and posting new ones."""
    if request.method == 'POST':
        if not check_authorization(request):
            return "Invalid authorization", 400

        message = request.json
        if not message or 'content' not in message or 'sender' not in message or 'timestamp' not in message:
            return "Invalid message format", 400

        # Save user's message
        messages = read_messages()
        messages.append(message)
        save_messages(messages)

        # Generate and save bot's reply
        bot_reply = {'content': eliza_response(message['content']), 'sender': 'EGGLIZA', 'timestamp': message['timestamp']}
        messages.append(bot_reply)
        save_messages(messages)

        return jsonify(bot_reply), 200
    else:
        if not check_authorization(request):
            return "Invalid authorization", 400
        return jsonify(read_messages()), 200

def read_messages():
    """Read messages from a JSON file."""
    try:
        with open(CHANNEL_FILE, 'r') as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_messages(messages):
    """Save messages to a JSON file."""
    with open(CHANNEL_FILE, 'w') as file:
        json.dump(messages, file)



if __name__ == '__main__':
    app.run(port=5003, debug=True)