import textwrap

from geopy import distance

from api.moltin_requests import fetch_cart_items, fetch_entries


NOTIFICATION_ABOUT_PIZZA = textwrap.dedent(
    f"""
    Приятного аппетита! *место для рекламы*

    *сообщение что делать если пицца не пришла*
    """
)


def calculate_delivery_cost(distance):
    """Calculate delivery cost based on distance

    Args:
        distance (float): distance in kilometers

    Returns:
        int: delivery cost
    """
    if distance <= 0.5:
        return 0
    if distance <= 5:
        return 100
    if distance <= 20:
        return 300
    return 0


def find_nearest_pizzeria(auth_token, client_coordinates):
    """Finds the closest pizzeria in terms of distance to the client

    Args:
        auth_token (str): authentication token
        client_coordinates (tuple): client current coordinates (lat, lon)

    Returns:
        dict: essential info about nearest pizzeria
    """
    fetched_pizzerias = fetch_entries(auth_token, 'pizzeria')

    pizzerias_with_distances = [
        dict(
            **pizzeria,
            **{
                'distance': distance.distance(
                    client_coordinates,
                    (pizzeria['latitude'], pizzeria['longitude']),
                ).kilometers
            },
        )
        for pizzeria in fetched_pizzerias['data']
    ]

    nearest_pizzeria = min(
        pizzerias_with_distances,
        key=lambda x: x['distance'],
    )

    attibutes_to_keep = ('address', 'distance', 'deliveryman_telegram_id')

    pizzeria_essential_info = {
        pizzeria_attribute: attribute_value
        for pizzeria_attribute, attribute_value in nearest_pizzeria.items()
        if pizzeria_attribute in attibutes_to_keep
    }

    return pizzeria_essential_info


def get_order_details_for_invoice(cart_id, context):
    """Gets order details for payment invoice

    Args:
        cart_id (str): id of client cart
        context: bot context

    Returns:
        tuple: order details and total invoice amount
    """
    auth_token = context.bot_data['auth_token'].token

    cart = fetch_cart_items(auth_token, f'pizza_{cart_id}')

    order_details = ''.join(
        '{}: {} шт; '.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )

    total_amount = cart['meta']['display_price']['without_tax']['amount']
    return (order_details, total_amount)


def notify_about_pizza(context):
    """Notifies client about not delivered pizza
    Args:
        context: bot context
    """
    context.bot.send_message(
        context.job.context,
        message=NOTIFICATION_ABOUT_PIZZA,
    )
