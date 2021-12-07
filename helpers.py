import time

from geopy import distance
from telegram.parsemode import ParseMode

from api.moltin_api_requests import (
    fetch_auth_token,
    fetch_cart_items,
    fetch_entries,
)
from interfaces import format_cart_for_deliveryman


def get_actual_auth_token(context, is_credentials=False):
    """Gets actual valid auth token. Returns current token from bot context if
    it's not yet expired, otherwise refreshes it in the context by requesting
    API and returns updated token.

    Args:
        context: bot context

    Returns:
        actual valid auth token
    """

    prefix = 'credentials' if is_credentials else 'implicit'

    expires = context.bot_data[f'{prefix}_token_expires']

    if expires - time.time() > 10:
        return context.bot_data[f'{prefix}_auth_token']

    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']

    params = (client_id, client_secret) if is_credentials else (client_id,)

    token_details = fetch_auth_token(*params)

    context.bot_data[f'{prefix}_token_expires'] = token_details['expires']
    context.bot_data[f'{prefix}_auth_token'] = token_details['access_token']

    return token_details['access_token']


def find_nearest_pizzeria(auth_token, client_coordinates):
    fetched_pizzerias = fetch_entries(auth_token, 'pizzeria')

    pizzerias_with_distances = {
        pizzeria['alias']: {
            'distance': distance.distance(
                client_coordinates,
                (pizzeria['latitude'], pizzeria['longitude']),
            ).kilometers,
            'pizzeria': pizzeria,
        }
        for pizzeria in fetched_pizzerias['data']
    }

    nearest_pizzeria = min(
        pizzerias_with_distances.items(),
        key=lambda x: x[1]['distance'],
    )

    return nearest_pizzeria


def send_order_details_to_deliveryman(cart_id, context):
    auth_token = get_actual_auth_token(context)
    cart = fetch_cart_items(auth_token, f'pizza_{cart_id}')
    cart_formatted = format_cart_for_deliveryman(cart)

    nearest_pizzeria = context.user_data['nearest_pizzeria']
    client_coordinates = context.user_data['client_coordinates']
    deliveryman_tg_id = nearest_pizzeria['deliveryman_telegram_id']

    context.bot.send_message(
        deliveryman_tg_id,
        text=cart_formatted,
        parse_mode=ParseMode.HTML,
    )
    context.bot.send_location(deliveryman_tg_id, **client_coordinates)
