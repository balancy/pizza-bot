import json

import requests

from helpers.fb_items_formatters import get_formatted_cart


def send_items(
    user_id, auth, fb_token, items_type, db=None, category_slug=None
):
    if items_type == 'cart':
        items = get_formatted_cart(auth, user_id)
    else:
        items = json.loads(db.get(category_slug).decode())

    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    request_content = {
        'recipient': {'id': user_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': items,
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


def send_message(user_id, message_text, fb_token):
    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}
    request_content = {
        'recipient': {'id': user_id},
        'message': {'text': message_text},
    }
    response = requests.post(
        'https://graph.facebook.com/v2.6/me/messages',
        params=params,
        headers=headers,
        json=request_content,
    )
    response.raise_for_status()
