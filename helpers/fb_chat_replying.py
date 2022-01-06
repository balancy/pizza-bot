import requests

from api.moltin_requests import fetch_categories, fetch_products_by_category_id
from helpers.fb_items_formatters import (
    format_first_menu_element,
    format_menu_element,
)


def find_category_id(auth_token, category_slug):
    all_categories = fetch_categories(auth_token)
    category = next(
        category
        for category in all_categories['data']
        if category['slug'] == category_slug
    )
    return category.get('id')


def send_menu(recipient_id, auth_token, fb_token):
    params = {'access_token': fb_token}
    headers = {'Content-Type': 'application/json'}

    category_id = find_category_id(auth_token, 'front_page')
    products = fetch_products_by_category_id(auth_token, category_id)

    elements = [
        format_menu_element(product, auth_token)
        for product in products['data']
    ]
    elements = [format_first_menu_element(), *elements]

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
