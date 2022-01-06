from enum import Enum

from api.moltin_requests import add_product_to_cart
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

    elif payload and state == State.MENU:
        if 'CATEGORY_ID' in payload:
            category_id = payload.replace('CATEGORY_ID_', '')
            send_menu(sender_id, auth_token, fb_token, category_id)
            return state

        elif 'ADD_TO_CART' in payload:
            product_id = payload.replace('ADD_TO_CART_', '')
            handle_adding_to_cart(product_id, sender_id, auth_token, fb_token)
            return state

        elif payload == 'CART':
            send_cart(sender_id, auth_token, fb_token)
            return State.CART

    elif payload and state == State.CART:
        if payload == 'BACK_TO_MENU':
            send_menu(sender_id, auth_token, fb_token)
            return State.MENU


def handle_adding_to_cart(product_id, sender_id, auth_token, fb_token):
    cart = add_product_to_cart(
        auth_token.token,
        f'fb_pizza_{sender_id}',
        product_id,
        1,
    )['data']

    product_name = list(
        filter(lambda product: product['product_id'] == product_id, cart)
    )[0]

    message = f'В корзину добавлена {product_name["name"]}'
    send_message(sender_id, message, fb_token)
