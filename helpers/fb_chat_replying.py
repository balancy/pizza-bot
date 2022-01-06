import requests

from helpers.fb_fetch_helpers import fetch_front_page_menu


def send_menu(recipient_id, auth_token, fb_token):
    front_page_menu = fetch_front_page_menu(auth_token)

    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    request_content = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': front_page_menu,
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


def send_button(recipient_id, fb_token):
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


def send_message(recipient_id, message_text, fb_token):
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
