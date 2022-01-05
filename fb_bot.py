import os

from dotenv import load_dotenv
from flask import Flask, request
import requests

from api.moltin_requests import fetch_image_by_id, fetch_products
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
                    send_menu(sender_id, auth_token.token)
    return "ok", 200


def send_button(recipient_id):
    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    request_content = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'button',
                    'text': 'Try the postback button!',
                    'buttons': [
                        {
                            'type': 'postback',
                            'title': 'Postback Button',
                            'payload': 'DEVELOPER_DEFINED_PAYLOAD',
                        }
                    ],
                },
            }
        },
    }

    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        headers=headers,
        params=params,
        json=request_content,
    )
    response.raise_for_status()


def get_menu_element(product, auth_token):
    product_price = product['meta']['display_price']['without_tax']['amount']
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = fetch_image_by_id(auth_token, product_image_id)['data']

    return {
        'title': f'{product["name"]} ({product_price} р.)',
        'image_url': product_image['link']['href'],
        'subtitle': product['description'],
        'buttons': [
            {
                'type': 'postback',
                'title': 'Добавить в корзину',
                'payload': f'ADD_{product["id"]}',
            }
        ],
    }


def send_menu(recipient_id, auth_token):
    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    products = fetch_products(auth_token)

    elements = [
        get_menu_element(product, auth_token)
        for product in products['data'][:5]
    ]

    request_content = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': elements,
                },
            },
        },
    }

    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        headers=headers,
        params=params,
        json=request_content,
    )
    response.raise_for_status()


def send_message(recipient_id, message_text):
    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}
    request_content = {
        'recipient': {'id': recipient_id},
        'message': {'text': message_text},
    }
    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        params=params,
        headers=headers,
        json=request_content,
    )
    response.raise_for_status()
