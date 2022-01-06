from enum import Enum

from api.moltin_requests import add_product_to_cart, remove_cart_item_by_id
from helpers.fb_chat_replying import send_items, send_message


class State(Enum):
    MENU = 1
    CART = 2


def handle_user_input(state, user_id, auth, fb_token, message, payload):
    if state == State.MENU and message:
        send_items(user_id, auth, fb_token, 'menu')
        return state

    if 'CATEGORY_ID' in payload and state == State.MENU:
        category_id = payload.replace('CATEGORY_ID_', '')
        send_items(user_id, auth, fb_token, 'menu', category_id)
        return state

    if 'ADD' in payload and state == State.MENU:
        handle_adding_to_cart(payload, user_id, auth, fb_token)
        return state

    if 'ADD' in payload and state == State.CART:
        handle_adding_to_cart(payload, user_id, auth, fb_token)
        send_items(user_id, auth, fb_token, 'cart')
        return state

    if 'REMOVE' in payload and state == State.CART:
        handle_removing_from_cart(payload, user_id, auth, fb_token)
        send_items(user_id, auth, fb_token, 'cart')
        return state

    if payload == 'CART':
        send_items(user_id, auth, fb_token, 'cart')
        return State.CART

    if payload == 'BACK_TO_MENU' and state == State.CART:
        send_items(user_id, auth, fb_token, 'menu')
        return State.MENU


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
