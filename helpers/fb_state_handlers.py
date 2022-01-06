from enum import Enum

from api.moltin_requests import add_product_to_cart
from helpers.fb_chat_replying import send_menu


class State(Enum):
    HANDLE_MENU = 1
    HANDLE_DESCRIPTION = 2
    HANDLE_CART = 3
    WAIT_EMAIL = 4
    HANDLE_COORDINATES = 5
    HANDLE_PAYMENT = 6


def handle_state(
    state,
    sender_id,
    auth_token,
    fb_token,
    message=None,
    payload=None,
):
    if state == State.HANDLE_MENU and message is not None:
        send_menu(sender_id, auth_token, fb_token)
    elif payload is not None:
        if state == State.HANDLE_MENU:
            category_id = payload.replace('CATEGORY_ID_', '')
            send_menu(sender_id, auth_token, fb_token, category_id)
            return state


        # product_id = payload.replace('ADD_TO_CART_', '')
        # cart = add_product_to_cart(
        #     auth_token.token,
        #     f'pizza_{sender_id}',
        #     product_id,
        #     1,
        # )
        # print(cart)
