import os

from dotenv import load_dotenv
from flask import Flask, request

from helpers.fb_action_handlers import handle_user_input, State
from helpers.token_handers import AuthToken


app = Flask(__name__)


@app.before_first_request
def start():
    load_dotenv()

    global auth, fb_token, state, verify_token

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth = AuthToken(client_id, client_secret)

    fb_token = os.getenv('PAGE_ACCESS_TOKEN')
    verify_token = os.getenv('VERIFY_TOKEN')
    state = State.MENU


@app.route('/', methods=['GET'])
def verify():
    """Verifies webhook for FB."""

    args = request.args
    if args.get('hub.mode') == 'subscribe' and args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == verify_token:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    return 'Hello world', 200


@app.route('/', methods=['POST'])
def webhook():
    """Webhook to handle facebook messages."""

    global state
    data = request.get_json()

    if data['object'] == 'page':
        for entry in data['entry']:
            for event in entry['messaging']:
                user_id = event['sender']['id']

                message = event.get('message')
                postback = event.get('postback')

                if message or postback:
                    message = message['text'] if message else None
                    payload = postback['payload'] if postback else None

                    state = handle_user_input(
                        state, user_id, auth, fb_token, message, payload
                    )

    return "ok", 200
