import json

from api.moltin_requests import (
    add_product_to_cart,
    fetch_categories,
    remove_cart_item_by_id,
)
from helpers.fb_chat_replying import send_items, send_message
from helpers.fb_items_formatters import get_formatted_menu


def handle_user_input(db, state, user_id, auth, fb_token, message, payload):
    if state == 'MENU' and message:
        send_items(user_id, auth, fb_token, 'menu', db, 'front_page')
        return state

    if payload and 'CATEGORY' in payload and state == 'MENU':
        category_slug = payload.replace('CATEGORY_', '')
        send_items(user_id, auth, fb_token, 'menu', db, category_slug)
        return state

    if payload and 'ADD' in payload and state == 'MENU':
        handle_adding_to_cart(payload, user_id, auth, fb_token)
        return state

    if payload and 'ADD' in payload and state == 'CART':
        handle_adding_to_cart(payload, user_id, auth, fb_token)
        send_items(user_id, auth, fb_token, 'cart')
        return state

    if payload and 'REMOVE' in payload and state == 'CART':
        handle_removing_from_cart(payload, user_id, auth, fb_token)
        send_items(user_id, auth, fb_token, 'cart')
        return state

    if payload == 'CART':
        send_items(user_id, auth, fb_token, 'cart')
        return 'CART'

    if payload == 'BACK_TO_MENU' and state == 'CART':
        send_items(user_id, auth, fb_token, 'menu', db, 'front_page')
        return 'MENU'


def handle_adding_to_cart(payload, user_id, auth, fb_token):
    payload = payload.replace('ADD_TO_CART_', '')
    product_id, product_name = payload.split('_')

    add_product_to_cart(auth.token, f'fb_pizza_{user_id}', product_id, 1)
    message = f'В корзину добавлена {product_name}'
    send_message(user_id, message, fb_token)


def handle_removing_from_cart(payload, user_id, auth, fb_token):
    payload = payload.replace('REMOVE_FROM_CART_', '')
    product_id, product_name = payload.split('_')

    remove_cart_item_by_id(auth.token, f'fb_pizza_{user_id}', product_id)

    message = f'{product_name} убрана из корзины'
    send_message(user_id, message, fb_token)


def handle_menu_caching(auth, db):
    categories = fetch_categories(auth.token)['data']
    for category in categories:
        slug = category['slug']
        menu = get_formatted_menu(auth, categories, slug)
        db.set(slug, json.dumps(menu))
