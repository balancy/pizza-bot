from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from api.api_requests import fetch_image_by_id


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

    caption = dedent(
        f"""
        <strong>{product_name}</strong>

        Стоимость: {product_price} рублей

        """
    )
    caption += product_description

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

    return dedent(
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

    if not bot_reply:
        bot_reply = 'Ваша корзина пуста'
    else:
        total_amount = cart['meta']['display_price']['without_tax']['amount']
        bot_reply = (
            f'<strong>Ваша корзина:</strong>\n\n'
            f'{bot_reply}\n'
            f'Всего: {total_amount} рублей'
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
    keyboard.append([InlineKeyboardButton('Оплатить', callback_data='Pay')])
    keyboard.append(
        [InlineKeyboardButton('Обратно в меню', callback_data='Back to menu')]
    )

    chat.reply_text(
        bot_reply,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode=ParseMode.HTML,
    )
