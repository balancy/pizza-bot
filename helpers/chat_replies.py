import textwrap

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from api.moltin_api_requests import fetch_image_by_id, fetch_cart_items
from helpers.items_formatting import (
    format_cart_item,
    format_delivery_options,
    format_order,
)
from helpers.utils import calculate_delivery_cost


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
    product_price = product['meta']['display_price']['without_tax']['amount']

    caption = textwrap.dedent(
        f"""
        <strong>{product['name']}</strong>

        Стоимость: {product_price} рублей

        """
    )
    caption = f'{caption}{product["description"]}'

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


def send_cart(cart, chat):
    """Send cart items list with keyboard to chat

    Args:
        cart: cart items dictionary
        chat: telegram chat instance to send cart items to
    """
    bot_reply = ''.join(
        format_cart_item(cart_item) for cart_item in cart['data']
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


def send_delivery_options(nearest_pizzeria, chat):
    """Send delivery options to chat

    Args:
        nearest_pizzeria: the closest pizzeria to client
        chat: chat to send delivery options to
    """
    distance = nearest_pizzeria['distance']
    delivery_cost = calculate_delivery_cost(distance)

    bot_reply = format_delivery_options(
        distance=distance,
        pizzeria_address=nearest_pizzeria['address'],
        delivery_cost=delivery_cost,
    )
    keyboard = [[InlineKeyboardButton('Самовывоз', callback_data='pickup')]]

    if distance > 20:
        return chat.reply_text(
            bot_reply,
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    keyboard.append(
        [InlineKeyboardButton('Доставка', callback_data='delivery')]
    )

    chat.reply_text(bot_reply, reply_markup=InlineKeyboardMarkup(keyboard))


def send_order_details(
    cart_id, auth_token, pizzeria, client_coordinates, delivery_cost, chat
):
    """Sends order details to the deliveryman

    Args:
        cart_id (str): id of client cart
        auth_token: authentication token
        pizzeria: nearest pizzeria
        client_coordinates: client coordinates (lat, lon)
        delivery_cost: cost of delivery in rubles
        chat: chat to send order details to
    """
    cart = fetch_cart_items(auth_token, f'pizza_{cart_id}')
    cart_formatted = format_order(cart, delivery_cost)

    deliveryman_tg_id = pizzeria['deliveryman_telegram_id']

    bot_reply = (
        f'<strong>Заказ от клиента {cart_id}</strong>\n\n{cart_formatted}'
    )

    chat.send_message(
        deliveryman_tg_id,
        text=bot_reply,
        parse_mode=ParseMode.HTML,
    )
    chat.send_location(deliveryman_tg_id, **client_coordinates)
