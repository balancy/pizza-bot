import os
from textwrap import dedent

from dotenv import load_dotenv
from telegram import LabeledPrice
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    Filters,
    MessageHandler,
    PicklePersistence,
    PreCheckoutQueryHandler,
    Updater,
)

from api.moltin_requests import (
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
from helpers.tg_chat_replying import (
    send_cart,
    send_delivery_options,
    send_order_details,
    send_product_details,
    send_products,
)
from helpers.delivery import (
    calculate_delivery_cost,
    find_nearest_pizzeria,
    get_order_details_for_invoice,
    notify_about_pizza,
)
from helpers.token_handers import AuthToken

(
    HANDLE_MENU,
    HANDLE_DESCRIPTION,
    HANDLE_CART,
    WAIT_EMAIL,
    HANDLE_COORDINATES,
    HANDLE_PAYMENT,
) = range(6)


def start(update, context):
    """Start handler.

    Returns:
        next bot state for user
    """
    chat = update.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = context.bot_data['auth_token'].token

    products = fetch_products(auth_token)
    send_products(products, chat)

    return HANDLE_MENU


def handle_menu(update, context):
    """Products menu handler.

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = context.bot_data['auth_token'].token

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, 'pizza_{}'.format(chat.chat_id))
        send_cart(cart, chat)

        return HANDLE_CART

    product = fetch_product_by_id(auth_token, query)['data']
    send_product_details(product, chat, auth_token)

    return HANDLE_DESCRIPTION


def handle_description(update, context):
    """Product description handler.

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = context.bot_data['auth_token'].token

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return HANDLE_MENU

    if query == 'Cart':
        cart = fetch_cart_items(auth_token, f'tg_pizza_{chat.chat_id}')
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
    """Client cart handler.

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    auth_token = context.bot_data['auth_token'].token

    if query == 'Back to menu':
        products = fetch_products(auth_token)
        send_products(products, chat)

        return HANDLE_MENU

    if query == 'Pay':
        chat.reply_text('?????????????? ?????? email')

        return WAIT_EMAIL

    cart = remove_cart_item_by_id(
        auth_token,
        'pizza_{}'.format(chat.chat_id),
        query,
    )
    send_cart(cart, chat)

    return HANDLE_CART


def wait_email(update, context):
    """Waits client email input.

    Returns:
        next bot state for user
    """
    chat = update.message or update.edited_message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)
    email = chat.text

    auth_token = context.bot_data['auth_token'].token

    try:
        create_customer(token=auth_token, email=email)
        bot_reply = f'???????????????????????? ?? email {email} ??????????????????????????????.'
    except EntityExistsError:
        bot_reply = f'???????????????????????? ?? email {email} ?????? ??????????????????????????????.'

    next_request = '???????????????? ?????? ?????? ?????????? ?????????????? ?????? ????????????????????.'
    chat.reply_text('{}\n{}'.format(bot_reply, next_request))

    return HANDLE_COORDINATES


def handle_incorrect_email(update, context):
    """Asks client for reentering his email.

    Returns:
        previous bot state for user
    """
    chat = update.message or update.edited_message
    chat.bot.delete_message(chat.chat_id, message_id=chat.message_id)

    bot_reply = '?????????????? ?????????? ?????? email. ?????????????? ???????????????? ???????? ????????????????????????.'
    chat.reply_text(bot_reply)

    return WAIT_EMAIL


def handle_address_or_location(update, context):
    """Handles entered address or location.

    Returns:
        next bot state for user
    """
    auth_token = context.bot_data['auth_token'].token
    yandex_token = context.bot_data['yandex_token']

    if location := update.message.location:
        position = (location.latitude, location.longitude)

    elif not (
        position := fetch_coordinates(yandex_token, update.message.text)
    ):
        update.message.reply_text(
            '???? ???????????????????? ???????????????????? ???????? ????????????????????. '
            '???????????????? ?????? ?????? ?????????? ?????????????? ?????? ????????????????????.'
        )

        return HANDLE_COORDINATES

    nearest_pizzeria = find_nearest_pizzeria(auth_token, position)
    context.user_data['nearest_pizzeria'] = nearest_pizzeria
    send_delivery_options(nearest_pizzeria, update.message)

    if None not in position:
        client_coordinates = {
            'latitude': position[0],
            'longitude': position[1],
        }
        context.user_data['client_coordinates'] = client_coordinates
        upload_entry(auth_token, client_coordinates, 'customer_address')

    return HANDLE_COORDINATES


def handle_delivery(update, context):
    """Handles client delivery choice.

    Returns:
        next bot state for user
    """
    query = update.callback_query.data
    chat = update.callback_query.message

    distance = context.user_data['nearest_pizzeria']['distance']
    delivery_cost = calculate_delivery_cost(distance)

    order_details, total_amount = get_order_details_for_invoice(
        cart_id=chat.chat_id,
        context=context,
    )

    context.user_data['delivery_option'] = query
    if query == 'pickup':
        user_choice = '??????????????????'
    else:
        user_choice = '????????????????'
        order_details = f'{order_details}????????????????: {delivery_cost}'
        total_amount += delivery_cost

    chat.reply_text(f'???? ?????????????? {user_choice}. ???????????? ???????????????? ?????? ??????????.')
    context.bot.send_invoice(
        chat_id=chat.chat_id,
        title='???????????? ???????????? ???? ????????????????',
        description=order_details,
        payload='pizza-bot-payload',
        provider_token=context.bot_data['payment_token'],
        currency='RUB',
        need_name=True,
        need_phone_number=True,
        prices=[LabeledPrice('?????????? ???? ????????????????', total_amount * 100)],
    )

    return HANDLE_PAYMENT


def handle_invoice_checking(update, context):
    """Checks if client invoice is correct.

    Returns:
        next bot state for user
    """
    query = update.pre_checkout_query
    if query.invoice_payload != 'pizza-bot-payload':
        query.answer(ok=False, error_message="??????-???? ?????????? ???? ??????...")
    else:
        query.answer(ok=True)

    return HANDLE_PAYMENT


def handle_payment(update, context):
    """Handles successful payment processing for client.

    Returns:
        end of conversation state
    """
    chat = update.message
    delivery_option = context.user_data['delivery_option']

    if delivery_option == 'pickup':
        pizzeria_address = context.user_data['nearest_pizzeria']['address']

        update.message.reply_text(
            dedent(
                f"""
            ???? ???????????? ?????????????? ?????? ?????????? ???? ????????????: {pizzeria_address}.
            ?????????????? ???? ??????????!"""
            )
        )
        return ConversationHandler.END

    distance = context.user_data['nearest_pizzeria']['distance']
    deliver_cost = calculate_delivery_cost(distance)
    client_coordinates = context.user_data['client_coordinates']
    nearest_pizzeria = context.user_data['nearest_pizzeria']
    auth_token = context.bot_data['auth_token'].token

    send_order_details(
        cart_id=chat.chat_id,
        auth_token=auth_token,
        pizzeria=nearest_pizzeria,
        client_coordinates=client_coordinates,
        delivery_cost=deliver_cost,
        chat=context.bot,
    )

    context.job_queue.run_once(notify_about_pizza, 3600, context=chat.chat_id)

    bot_reply = '???????????????????? ?? ???????????? ???????????????? ??????????????. ?????????????? ???? ??????????!'
    update.message.reply_text(bot_reply)

    return ConversationHandler.END


def exit(update, context):
    """User fallback handler

    Args:
        update and context: standard bot handler args

    Returns:
        end of conversation state
    """
    update.message.reply_text('???? ?????????????????? ????????????')

    return ConversationHandler.END


if __name__ == '__main__':
    load_dotenv()

    bot_token = os.getenv('TG_PIZZA_BOT_TOKEN')
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    persistence = PicklePersistence(filename='conversationbot')
    updater = Updater(bot_token, use_context=True, persistence=persistence)
    jq = updater.job_queue

    dp = updater.dispatcher
    dp.bot_data['yandex_token'] = os.getenv('YANDEX_API_TOKEN')
    dp.bot_data['payment_token'] = os.getenv('PAYMENT_PROVIDER_TOKEN')
    dp.bot_data['auth_token'] = AuthToken(client_id, client_secret)

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
                MessageHandler(
                    Filters.location | Filters.text,
                    handle_address_or_location,
                ),
                CallbackQueryHandler(handle_delivery),
            ],
            HANDLE_PAYMENT: [
                PreCheckoutQueryHandler(handle_invoice_checking),
                MessageHandler(
                    Filters.successful_payment,
                    handle_payment,
                    pass_job_queue=True,
                ),
            ],
        },
        fallbacks=[CommandHandler('exit', exit)],
        persistent=True,
        name='conversation_handler',
        per_chat=False,
    )

    dp.add_handler(handler)

    updater.start_polling()
    updater.idle()
