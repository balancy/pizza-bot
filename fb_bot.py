import os

from dotenv import load_dotenv
from flask import Flask, request

from helpers.fb_state_handlers import State, handle_state
from helpers.token_handers import AuthToken


app = Flask(__name__)


@app.before_first_request
def start():
    load_dotenv()

    global auth_token, fb_token, state, verify_token

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth_token = AuthToken(client_id, client_secret)

    fb_token = os.getenv('PAGE_ACCESS_TOKEN')
    verify_token = os.getenv('VERIFY_TOKEN')
    state = State.HANDLE_MENU


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

    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for event in entry['messaging']:
                sender_id = event['sender']['id']
                if message := event.get('message'):
                    handle_state(
                        state=state,
                        sender_id=sender_id,
                        auth_token=auth_token,
                        fb_token=fb_token,
                        message=message['text'],
                    )
                elif postback := event.get('postback'):
                    handle_state(
                        state=state,
                        sender_id=sender_id,
                        auth_token=auth_token,
                        fb_token=fb_token,
                        payload=postback['payload'],
                    )
    return "ok", 200
