import textwrap
import time

from geopy import distance
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode
from telegram.parsemode import ParseMode

from api.moltin_api_requests import (
    fetch_auth_token,
    fetch_cart_items,
    fetch_entries,
    fetch_image_by_id,
)


NOTIFICATION_ABOUT_PIZZA = textwrap.dedent(
    f"""
    Приятного аппетита! *место для рекламы*

    *сообщение что делать если пицца не пришла*
    """
)


def send_products(products, chat):
    """Send products list with keyboard to the chat.

    Args:
        products: products dictionary
        chat: telegram chat instance to send products to
    """
    keyboard = [
        [InlineKeyboardButton(product['name'], callback_data=product['id'])]
        for product in products['data']
    ]
    keyboard.append([InlineKeyboardButton('Корзина', callback_data='Cart')])

    chat.reply_text('Каталог', reply_markup=InlineKeyboardMarkup(keyboard))


def send_product_details(product, chat, auth_token):
    """Send product details with keyboard to the chat.

    Args:
        product: product details dictionary
        chat: telegram chat instance to send product details to
        auth_token: bearer token to request a product image
    """
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = fetch_image_by_id(auth_token, product_image_id)['data']
    product_image_url = product_image['link']['href']

    product_id = product['id']
    product_name = product['name']
    product_price = product['meta']['display_price']['without_tax']['amount']
    product_description = product['description']

    caption = textwrap.dedent(
        f"""
        <strong>{product_name}</strong>

        Стоимость: {product_price} рублей

        """
    )
    caption = f'{caption}{product_description}'

    keyboard = [
        [
            InlineKeyboardButton(
                f'{quantity} шт',
                callback_data=f'{product_id};{quantity}',
            )
            for quantity in [1, 5, 10]
        ],
        [
            InlineKeyboardButton(
                'Обратно в меню', callback_data='Back to menu'
            ),
            InlineKeyboardButton('Корзина', callback_data='Cart'),
        ],
    ]

    chat.bot.send_photo(
        chat.chat_id,
        product_image_url,
        caption=caption,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )


def format_cart_item_for_display(cart_item):
    """Transfrom cart item dicionary to formatted string

    Args:
        cart_item: cart item dicionary

    Returns:
        formatted string
    """
    name = cart_item['name']
    formatted_price = cart_item['meta']['display_price']['without_tax']
    unit_price = formatted_price['unit']['amount']
    position_price = formatted_price['value']['amount']
    quantity = cart_item['quantity']

    return textwrap.dedent(
        f"""\
        <strong>{name}</strong>
        Цена: {unit_price} рублей за штуку
        Штук в корзине: {quantity} на сумму {position_price} рублей

        """
    )


def send_cart(cart, chat):
    """Send cart items list with keyboard to chat

    Args:
        cart: cart items dictionary
        chat: telegram chat instance to send cart items to
    """
    bot_reply = ''.join(
        format_cart_item_for_display(cart_item) for cart_item in cart['data']
    )

    keyboard = [
        [
            InlineKeyboardButton(
                f'Убрать "{cart_item["name"]}" из корзины',
                callback_data=f'{cart_item["id"]}',
            )
        ]
        for cart_item in cart['data']
    ]

    if not bot_reply:
        bot_reply = 'Ваша корзина пуста'
    else:
        total_amount = cart['meta']['display_price']['without_tax']['amount']
        bot_reply = (
            f'<strong>Ваша корзина:</strong>\n\n'
            f'{bot_reply}'
            f'<strong>Всего: {total_amount} рублей</strong>'
        )
        keyboard.append(
            [InlineKeyboardButton('Оплатить', callback_data='Pay')]
        )

    keyboard.append(
        [InlineKeyboardButton('Обратно в меню', callback_data='Back to menu')]
    )

    chat.reply_text(
        bot_reply,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
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


def send_delivery_options(nearest_pizzeria, chat):
    """Send delivery options to chat

    Args:
        nearest_pizzeria: the closest pizzeria to client
        chat: chat to send delivery options to
    """
    distance = nearest_pizzeria['distance']
    delivery_cost = calculate_delivery_cost(distance)

    keyboard = [
        [
            InlineKeyboardButton('Самовывоз', callback_data='pickup'),
        ],
    ]

    if distance > 20:
        return chat.reply_text(
            textwrap.dedent(
                f"""
                Простите, но так далеко мы пиццу не доставляем. Ближайшая
                пиццерия находится в {distance:.1f} километрах от Вас! Возможен
                только самовывоз
                """
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    keyboard.append(
        [
            InlineKeyboardButton('Доставка', callback_data='delivery'),
        ],
    )

    if distance <= 0.5:
        return chat.reply_text(
            textwrap.dedent(
                f"""
                Может, заберете пиццу из нашей пиццерии неподалёку?
                Она всего в {round(distance * 1000)} метрах от вас!
                Вот её адрес: {nearest_pizzeria['address']}.

                Также возможен вариант бесплатной доставки.
                """
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    if distance <= 5:
        return chat.reply_text(
            textwrap.dedent(
                f"""
                Похоже, придётся ехать до Вас на самокате. Доставка
                будет стоить {delivery_cost} рублей. Доставляем или самовывоз?
                """
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return chat.reply_text(
        textwrap.dedent(
            f"""
            Похоже, придётся ехать до Вас на авто. Доставка будет
            стоить {delivery_cost} рублей. Доставляем или самовывоз?
            """
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def format_order_for_deliveryman(cart, delivery_cost):
    """Format order details for deliveryman

    Args:
        cart (dictionary): client current cart as order details
        deliver_cost: cost of delivery

    Returns:
        str: order details in formatted form
    """
    cart_positions = ''.join(
        '{}: {} шт\n'.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )
    cart_positions = '{}Плата за доставку: {} рублей\n'.format(
        cart_positions,
        delivery_cost,
    )

    total_amount = cart['meta']['display_price']['without_tax']['amount']
    total_amount += delivery_cost

    return '{}\n<strong>Всего к оплате: {} рублей</strong>'.format(
        cart_positions,
        total_amount,
    )


def format_order_details_for_invoice(cart):
    """Format order details for payment invoice

    Args:
        cart (dictionary): client current cart as order details

    Returns:
        str: order details in formatted form
    """
    return ''.join(
        '{}: {} шт; '.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )


def get_actual_auth_token(context, is_credentials=False):
    """Gets actual valid auth token. Returns current token from bot context if
    it's not yet expired, otherwise refreshes it in the context by requesting
    API and returns updated token.

    Args:
        context: bot context
        is_credentials: if token needs to be of 'client_credentials' type

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

    keys_to_keep = ('address', 'distance', 'deliveryman_telegram_id')

    pizzeria_essential_info = {
        key: value
        for key, value in nearest_pizzeria.items()
        if key in keys_to_keep
    }

    return pizzeria_essential_info


def send_order_details_to_deliveryman(cart_id, context, delivery_cost):
    """Sends order details to the deliveryman

    Args:
        cart_id (str): id of client cart
        context: bot context
        delivery_cost: cost of delivery in rubles
    """
    auth_token = get_actual_auth_token(context)
    cart = fetch_cart_items(auth_token, f'pizza_{cart_id}')
    cart_formatted = format_order_for_deliveryman(cart, delivery_cost)

    nearest_pizzeria = context.user_data['nearest_pizzeria']
    client_coordinates = context.user_data['client_coordinates']
    deliveryman_tg_id = nearest_pizzeria['deliveryman_telegram_id']

    bot_reply = (
        f'<strong>Заказ от клиента {cart_id}</strong>\n\n{cart_formatted}'
    )

    context.bot.send_message(
        deliveryman_tg_id,
        text=bot_reply,
        parse_mode=ParseMode.HTML,
    )
    context.bot.send_location(deliveryman_tg_id, **client_coordinates)


def get_order_details_for_invoice(cart_id, context):
    """Gets order details for payment invoice

    Args:
        cart_id (str): id of client cart
        context: bot context

    Returns:
        tuple: order details and total invoice amount
    """
    auth_token = get_actual_auth_token(context)
    cart = fetch_cart_items(auth_token, f'pizza_{cart_id}')
    order_details = format_order_details_for_invoice(cart)

    total_amount = cart['meta']['display_price']['without_tax']['amount']
    return (order_details, total_amount)


def notify_about_pizza(context):
    """Notifies client about not delivered pizza

    Args:
        context: bot context
    """
    context.bot.send_message(
        context.job.context,
        text=NOTIFICATION_ABOUT_PIZZA,
    )
