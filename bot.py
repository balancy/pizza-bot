import os
import time
from textwrap import dedent

from dotenv import load_dotenv
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    Updater,
)

from api.moltin_api_requests import (
    add_product_to_cart,
    create_customer,
    fetch_cart_items,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
    upload_entry,
    EntityExistsError,
)
from api.yandex_api_requests import fetch_coordinates
from helpers import (
    find_nearest_pizzeria,
    get_actual_auth_token,
    send_order_details_to_deliveryman,
)
from interfaces import (
    send_cart,
    send_delivery_options,
    send_product_details,
    send_products,
)


(
    HANDLE_MENU,
    HANDLE_DESCRIPTION,
    HANDLE_CART,
    WAIT_EMAIL,
    HANDLE_COORDINATES,
) = range(5)


def start(update, context):
    """Start handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    chat = update.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = get_actual_auth_token(context)

    products = fetch_products(auth_token)
    send_products(products, chat)

    return HANDLE_MENU


def handle_menu(update, context):
    """Products menu handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = get_actual_auth_token(context)

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, 'pizza_{}'.format(chat.chat_id))
        send_cart(cart, chat)

        return HANDLE_CART

    product = fetch_product_by_id(auth_token, query)['data']
    send_product_details(product, chat, auth_token)

    return HANDLE_DESCRIPTION


def handle_description(update, context):
    """Product description handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = get_actual_auth_token(context)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return HANDLE_MENU

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, 'pizza_{}'.format(chat.chat_id))
        send_cart(cart, chat)

        return HANDLE_CART

    product_id, quantity = query.split(';')
    cart = add_product_to_cart(
        auth_token,
        'pizza_{}'.format(chat.chat_id),
        product_id,
        int(quantity),
    )

    send_cart(cart, chat)

    return HANDLE_CART


def handle_cart(update, context):
    """User cart handler

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = get_actual_auth_token(context)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return HANDLE_MENU

    if query == 'Pay':
        chat.reply_text('Введите ваш email')

        return WAIT_EMAIL

    cart = remove_cart_item_by_id(
        auth_token,
        'pizza_{}'.format(chat.chat_id),
        query,
    )
    send_cart(cart, chat)

    return HANDLE_CART


def wait_email(update, context):
    """Waiting user email input handler

    Args:
        update and context: standard bot handler args

    Returns:
        end of conversation state
    """
    chat = update.message or update.edited_message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)
    email = chat.text

    auth_token = get_actual_auth_token(context)

    try:
        create_customer(token=auth_token, email=email)
    except EntityExistsError:
        bot_reply = f'Пользователь с email {email} уже зарегистрирован.'
    else:
        bot_reply = f'Пользователь с email {email} зарегистрирован.'

    next_request = 'Пришлите нам Ваш адрес текстом или геолокацию.'
    chat.reply_text('{}\n{}'.format(bot_reply, next_request))

    return HANDLE_COORDINATES


def handle_incorrect_email(update, context):
    """Demands user to reenter his email.

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    chat = update.message or update.edited_message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    bot_reply = 'Введите снова Ваш email. Кажется введеный Вами неправильный.'
    chat.reply_text(bot_reply)

    return WAIT_EMAIL


def handle_address_or_location(update, context):
    auth_token = get_actual_auth_token(context)
    yandex_token = context.bot_data['yandex_token']

    if location := update.message.location:
        position = (location.latitude, location.longitude)

    elif not (
        position := fetch_coordinates(yandex_token, update.message.text)
    ):
        update.message.reply_text(
            'Не получилось определить ваши координаты. '
            'Пришлите нам Ваш адрес текстом или геолокацию.'
        )

        return HANDLE_COORDINATES

    nearest_pizzeria = find_nearest_pizzeria(auth_token, position)
    context.user_data['nearest_pizzeria'] = nearest_pizzeria[1]['pizzeria']
    send_delivery_options(nearest_pizzeria, update.message)

    auth_token = get_actual_auth_token(context, is_credentials=True)
    client_coordinates = {'latitude': position[0], 'longitude': position[1]}
    context.user_data['client_coordinates'] = client_coordinates
    upload_entry(auth_token, client_coordinates, 'customer_address')

    return HANDLE_COORDINATES


def handle_delivery(update, context):
    query = update.callback_query.data
    chat = update.callback_query.message

    if query == 'pickup':
        nearest_pizzeria = context.user_data['nearest_pizzeria']

        bot_reply = dedent(
            f"""
            Вы выбрали самовывоз. Вы можете забрать Ваз заказ по адресу:
            {nearest_pizzeria['address']}. Спасибо за заказ!"""
        )
        chat.reply_text(bot_reply)

        return ConversationHandler.END

    chat.reply_text(
        dedent(
            """
            Вы выбрали доставку. Информация о заказе передана курьеру.
            Спасибо за заказ!"""
        )
    )
    send_order_details_to_deliveryman(cart_id=chat.chat_id, context=context)

    return ConversationHandler.END


def exit(update, context):
    """User fallback handler

    Args:
        update and context: standard bot handler args

    Returns:
        end of conversation state
    """
    update.message.reply_text('Вы закончили диалог')

    return ConversationHandler.END


if __name__ == '__main__':
    load_dotenv()

    bot_token = os.getenv('TG_PIZZA_BOT_TOKEN')

    # persistence = PicklePersistence(filename='conversationbot')
    # updater = Updater(bot_token, use_context=True, persistence=persistence)
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.bot_data['client_id'] = os.getenv('CLIENT_ID')
    dp.bot_data['client_secret'] = os.getenv('CLIENT_SECRET')
    dp.bot_data['yandex_token'] = os.getenv('YANDEX_API_TOKEN')
    dp.bot_data['implicit_auth_token'] = ''
    dp.bot_data['credentials_auth_token'] = ''
    dp.bot_data['implicit_token_expires'] = time.time()
    dp.bot_data['credentials_token_expires'] = time.time()

    handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            HANDLE_MENU: [CallbackQueryHandler(handle_menu)],
            HANDLE_DESCRIPTION: [CallbackQueryHandler(handle_description)],
            HANDLE_CART: [CallbackQueryHandler(handle_cart)],
            WAIT_EMAIL: [
                MessageHandler(Filters.regex('^\w+@\w+\.\w+$'), wait_email),
                MessageHandler(Filters.text, handle_incorrect_email),
            ],
            HANDLE_COORDINATES: [
                MessageHandler(Filters.location, handle_address_or_location),
                MessageHandler(Filters.text, handle_address_or_location),
                CallbackQueryHandler(handle_delivery),
            ],
        },
        fallbacks=[CommandHandler('exit', exit)],
        persistent=False,
        name='conversation_handler',
    )

    dp.add_handler(handler)

    updater.start_polling()
    updater.idle()
