from enum import Enum

from api.moltin_requests import add_product_to_cart, remove_cart_item_by_id
from helpers.fb_chat_replying import send_cart, send_menu, send_message


class State(Enum):
    MENU = 1
    CART = 2
    WAIT_EMAIL = 3
    COORDINATES = 4
    PAYMENT = 5


def handle_state(
    state,
    sender_id,
    auth_token,
    fb_token,
    message=None,
    payload=None,
):
    if state == State.MENU and message:
        send_menu(sender_id, auth_token, fb_token)
        return state

    if 'CATEGORY_ID' in payload and state == State.MENU:
        category_id = payload.replace('CATEGORY_ID_', '')
        send_menu(sender_id, auth_token, fb_token, category_id)
        return state

    if 'ADD' in payload and state == State.MENU:
        handle_adding_to_cart(payload, sender_id, auth_token, fb_token)
        return state

    if 'ADD' in payload and state == State.CART:
        handle_adding_to_cart(payload, sender_id, auth_token, fb_token)
        send_cart(sender_id, auth_token, fb_token)
        return state

    if 'REMOVE' in payload and state == State.CART:
        handle_removing_from_cart(payload, sender_id, auth_token, fb_token)
        send_cart(sender_id, auth_token, fb_token)
        return state

    if payload == 'CART':
        send_cart(sender_id, auth_token, fb_token)
        return State.CART

    if payload == 'BACK_TO_MENU' and state == State.CART:
        send_menu(sender_id, auth_token, fb_token)
        return State.MENU


def handle_adding_to_cart(payload, sender_id, auth_token, fb_token):
    payload = payload.replace('ADD_TO_CART_', '')
    product_id, product_name = payload.split('_')

    add_product_to_cart(
        auth_token.token,
        f'fb_pizza_{sender_id}',
        product_id,
        1,
    )
    message = f'В корзину добавлена {product_name}'
    send_message(sender_id, message, fb_token)


def handle_removing_from_cart(payload, sender_id, auth_token, fb_token):
    payload = payload.replace('REMOVE_FROM_CART_', '')
    product_id, product_name = payload.split('_')

    remove_cart_item_by_id(
        auth_token.token,
        f'fb_pizza_{sender_id}',
        product_id,
    )

    message = f'{product_name} убрана из корзины'
    send_message(sender_id, message, fb_token)
