import os

from dotenv import load_dotenv
from flask import Flask, request
import requests

load_dotenv()

app = Flask(__name__)

FACEBOOK_TOKEN = os.getenv('PAGE_ACCESS_TOKEN')
VERIFY_TOKEN = os.getenv('VERIFY_TOKEN')


@app.route('/', methods=['GET'])
def verify():
    """Verifies webhook for FB."""
    args = request.args
    if args.get('hub.mode') == 'subscribe' and args.get('hub.challenge'):
        if not args.get('hub.verify_token') == VERIFY_TOKEN:
            return 'Verification token mismatch', 403
        return args['hub.challenge'], 200

    return 'Hello world', 200


@app.route('/', methods=['POST'])
def webhook():
    """Webhook to handle facebook messages."""
    data = request.get_json()
    if data['object'] == 'page':
        for entry in data['entry']:
            for messaging_event in entry['messaging']:
                if messaging_event.get('message'):
                    sender_id = messaging_event['sender']['id']
                    message_text = messaging_event['message']['text']
                    send_message(sender_id, message_text)
    return 'ok', 200


def send_message(recipient_id, message_text):
    params = {"access_token": FACEBOOK_TOKEN}
    headers = {"Content-Type": "application/json"}
    request_content = {
        "recipient": {"id": recipient_id},
        "message": {"text": message_text},
    }
    response = requests.post(
        "https://graph.facebook.com/v2.6/me/messages",
        params=params,
        headers=headers,
        json=request_content,
    )
    response.raise_for_status()


if __name__ == '__main__':
    app.run(debug=True)
