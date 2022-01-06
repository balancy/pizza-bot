from api.moltin_requests import fetch_image_by_id


def format_menu_element(product, auth_token):
    product_price = product['meta']['display_price']['without_tax']['amount']
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = fetch_image_by_id(auth_token, product_image_id)['data']

    return {
        'title': f'{product["name"]} ({product_price} р.)',
        'image_url': product_image['link']['href'],
        'subtitle': product['description'],
        'buttons': [
            {
                'type': 'postback',
                'title': 'Добавить в корзину',
                'payload': f'ADD_TO_CART_{product["id"]}_{product["name"]}',
            }
        ],
    }


def format_cart_element(product):
    unit_price = product['unit_price']['amount']
    value_price = product['value']['amount']
    quantity = product['quantity']

    image_url = product['image']['href']

    return {
        'title': f'{product["name"]} ({unit_price} р., {quantity} шт.)',
        'image_url': image_url,
        'subtitle': f'Всего на {value_price} рублей',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Добавить еще одну',
                'payload': f'ADD_TO_CART_{product["product_id"]}_'
                f'{product["name"]}',
            },
            {
                'type': 'postback',
                'title': 'Убрать из корзины',
                'payload': f'REMOVE_FROM_CART_{product["id"]}_'
                f'{product["name"]}',
            },
        ],
    }


def format_first_menu_element():
    return {
        'title': 'Меню',
        'image_url': 'https://cdn.pixabay.com/photo/2013/07/13/13/18/'
        'pizza-160780_1280.png',
        'subtitle': 'Здесь Вы можете выбрать один из вариантов',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Корзина',
                'payload': 'CART',
            },
            {
                'type': 'postback',
                'title': 'Акции',
                'payload': 'ACTIONS',
            },
            {
                'type': 'postback',
                'title': 'Сделать заказ',
                'payload': 'MAKE_ORDER',
            },
        ],
    }


def format_first_cart_element(price):
    return {
        'title': f'Заказ на сумму {price} руб.',
        'image_url': 'https://postium.ru/wp-content/uploads/2018/08/'
        'idealnaya-korzina-internet-magazina-1068x713.jpg',
        'buttons': [
            {
                'type': 'postback',
                'title': 'Самовывоз',
                'payload': 'PICKUP',
            },
            {
                'type': 'postback',
                'title': 'Доставка',
                'payload': 'DELIVERY',
            },
            {
                'type': 'postback',
                'title': 'Обратно в меню',
                'payload': 'BACK_TO_MENU',
            },
        ],
    }


def format_last_menu_element(categories):
    return {
        'title': 'Не нашли нужную пиццу?',
        'image_url': 'https://primepizza.ru/uploads/position/'
        'large_0c07c6fd5c4dcadddaf4a2f1a2c218760b20c396.jpg',
        'subtitle': 'Остальные пиццы можно посмотреть в категориях:',
        'buttons': [
            {
                'type': 'postback',
                'title': category['name'],
                'payload': f'CATEGORY_ID_{category["id"]}',
            }
            for category in categories
        ],
    }
