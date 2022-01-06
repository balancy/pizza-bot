import requests

from api.moltin_requests import fetch_categories, fetch_products_by_category_id
from helpers.fb_items_formatters import (
    format_first_menu_element,
    format_last_menu_element,
    format_menu_element,
)


def send_menu(recipient_id, auth_token, fb_token):
    categories = fetch_categories(auth_token)['data']

    first_category = next(
        filter(lambda category: category['slug'] == 'front_page', categories)
    )

    other_categories = list(
        filter(lambda category: category['slug'] != 'front_page', categories)
    )

    products = fetch_products_by_category_id(
        auth_token, first_category.get('id')
    )['data']

    menu_elements = [
        format_first_menu_element(),
        *[format_menu_element(product, auth_token) for product in products],
        format_last_menu_element(other_categories),
    ]

    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    request_content = {
        'recipient': {'id': recipient_id},
        'message': {
            'attachment': {
                'type': 'template',
                'payload': {
                    'template_type': 'generic',
                    'elements': menu_elements,
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
