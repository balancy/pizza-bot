import os
import time

from dotenv import load_dotenv
from telegram import KeyboardButton, ReplyKeyboardMarkup
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
    fetch_auth_token,
    fetch_cart_items,
    fetch_products,
    fetch_product_by_id,
    remove_cart_item_by_id,
    EntityExistsError,
)
from api.yandex_api_requests import fetch_coordinates
from interfaces import send_cart, send_product_details, send_products


(
    HANDLE_MENU,
    HANDLE_DESCRIPTION,
    HANDLE_CART,
    WAIT_EMAIL,
    WAIT_COORDINATES,
) = range(5)


def get_actual_auth_token(context):
    """Gets actual valid auth token. Returns current token from bot context if
    it's not yet expired, otherwise refreshes it in the context by requesting
    API and returns updated token.

    Args:
        context: bot context

    Returns:
        actual valid auth token
    """
    expires = context.bot_data['token_expires']

    if expires - time.time() > 10:
        return context.bot_data['auth_token']

    client_id = context.bot_data['client_id']
    token_details = fetch_auth_token(client_id)

    context.bot_data['token_expires'] = token_details['expires']
    context.bot_data['auth_token'] = token_details['access_token']

    return token_details['access_token']


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

    auth_token = get_actual_auth_token(context)

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

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

    auth_token = get_actual_auth_token(context)

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return HANDLE_MENU

    elif query == 'Cart':
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

    auth_token = get_actual_auth_token(context)

    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

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
    bot_message = update.message or update.edited_message
    query = bot_message.text

    auth_token = get_actual_auth_token(context)

    try:
        create_customer(token=auth_token, email=query)
    except EntityExistsError:
        bot_reply = f'Пользователь с email {query} уже зарегистрирован.'
    else:
        bot_reply = f'Вы успешно зарегистрированы.'

    next_request = 'Хорошо. Пришлите нам Ваш адрес текстом или геолокацию.'
    bot_message.reply_text('{}\n{}'.format(bot_reply, next_request))

    return WAIT_COORDINATES


def handle_incorrect_email(update, context):
    """Demands user to reenter his email.

    Args:
        update and context: standard bot handler args

    Returns:
        next bot state for user
    """
    bot_message = update.message or update.edited_message

    bot_reply = 'Введите снова ваш email. Кажется введеный вами неправильный.'
    bot_message.reply_text(bot_reply)

    return WAIT_EMAIL


def handle_location(update, context):
    location = update.message.location
    position = (location.latitude, location.longitude)
    update.message.reply_text('({}, {})'.format(*position))

    return ConversationHandler.END


def wait_coordinates(update, context):
    yandex_token = context.bot_data['yandex_token']

    query = update.message.text
    position = fetch_coordinates(yandex_token, query)

    if position:
        update.message.reply_text('({}, {})'.format(*position))

        return ConversationHandler.END
    else:
        update.message.reply_text(
            'Не получилось определить ваши координаты. '
            'Пришлите нам Ваш адрес текстом или геолокацию.'
        )

        return WAIT_COORDINATES


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
    moltin_client_id = os.getenv('CLIENT_ID')
    yandex_token = os.getenv('YANDEX_API_TOKEN')

    # persistence = PicklePersistence(filename='conversationbot')
    # updater = Updater(bot_token, use_context=True, persistence=persistence)
    updater = Updater(bot_token, use_context=True)
    dp = updater.dispatcher
    dp.bot_data['client_id'] = moltin_client_id
    dp.bot_data['yandex_token'] = yandex_token
    dp.bot_data['auth_token'] = ''
    dp.bot_data['token_expires'] = time.time()

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
            WAIT_COORDINATES: [
                MessageHandler(Filters.location, handle_location),
                MessageHandler(Filters.text, wait_coordinates),
            ],
        },
        fallbacks=[CommandHandler('exit', exit)],
        persistent=False,
        name='conversation_handler',
    )

    dp.add_handler(handler)

    updater.start_polling()
    updater.idle()
