import os

from dotenv import load_dotenv
from flask import Flask, request

from helpers.fb_chat_replying import send_menu
from helpers.token_handers import AuthToken


app = Flask(__name__)


@app.before_first_request
def start():
    load_dotenv()

    global auth_token, client_id, client_secret, fb_token, verify_token

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    fb_token = os.getenv('PAGE_ACCESS_TOKEN')
    verify_token = os.getenv('VERIFY_TOKEN')
    auth_token = AuthToken(client_id, client_secret)


@app.route('/', methods=['GET'])
def verify():
    """Verifies webhook for FB."""

    args = request.args
    if args.get("hub.mode") == "subscribe" and args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == verify_token:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    """Webhook to handle facebook messages."""

    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    message_text = messaging_event["message"]["text"]
                    send_menu(sender_id, auth_token.token, fb_token)
    return "ok", 200
