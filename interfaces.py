from textwrap import dedent

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode

from api.moltin_api_requests import fetch_image_by_id


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

    return bot_reply


def send_delivery_options(nearest_pizzeria, chat):
    distance = nearest_pizzeria[1]['distance']

    keyboard = [
        [
            InlineKeyboardButton('Самовывоз', callback_data='pickup'),
        ],
    ]

    if distance > 20:
        return chat.reply_text(
            dedent(
                f"""
                Простите, но так далеко мы пиццу не доставляем. Ближайшая
                пиццерия находится в {distance:.1f} километрах от Вас! Возможен
                только самовывоз"""
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
            dedent(
                f"""
                Может, заберете пиццу из нашей пиццерии неподалёку?
                Она всего в {round(distance * 1000)} метрах от вас!
                Вот её адрес: {nearest_pizzeria[1]['address']}.

                Также возможен вариант бесплатной доставки."""
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    if distance <= 5:
        return chat.reply_text(
            dedent(
                """
                Похоже, придётся ехать до Вас на самокате. Доставка
                будет стоить 100 рублей. Доставляем или самовывоз?"""
            ),
            reply_markup=InlineKeyboardMarkup(keyboard),
        )

    return chat.reply_text(
        dedent(
            """
            Похоже, придётся ехать до Вас на авто. Доставка будет
            стоить 300 рублей. Доставляем или самовывоз?"""
        ),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


def format_cart_for_deliveryman(cart):
    cart_positions = ''.join(
        '{}: {} шт\n'.format(cart_item['name'], cart_item['quantity'])
        for cart_item in cart['data']
    )
    total_amount = cart['meta']['display_price']['without_tax']['amount']

    return '{}\n<strong>Всего к оплате: {} рублей</strong>'.format(
        cart_positions,
        total_amount,
    )
