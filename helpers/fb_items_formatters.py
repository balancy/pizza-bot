from api.moltin_requests import (
    fetch_cart_items,
    fetch_categories,
    fetch_image_by_id,
    fetch_products_by_category_id,
)


def format_menu(auth, category_id):
    categories = fetch_categories(auth.token)['data']

    if not category_id:
        displaying_category = next(
            filter(
                lambda category: category['slug'] == 'front_page',
                categories,
            )
        )
        category_id = displaying_category.get('id')

    other_categories = list(
        filter(lambda category: category['id'] != category_id, categories)
    )

    products = fetch_products_by_category_id(auth.token, category_id)['data']

    products_formatted = [
        format_menu_element(product, auth) for product in products
    ]

    front_page_menu = [
        format_first_menu_element(),
        *products_formatted,
        format_last_menu_element(other_categories),
    ]

    return front_page_menu


def format_cart(auth, recepient_id):
    cart = fetch_cart_items(auth.token, f'fb_pizza_{recepient_id}')

    cart_items_formatted = [format_cart_element(item) for item in cart['data']]

    total_price = cart['meta']['display_price']['without_tax']['amount']

    return [
        format_first_cart_element(total_price),
        *cart_items_formatted,
    ]


def format_menu_element(product, auth):
    product_price = product['meta']['display_price']['without_tax']['amount']
    product_image_id = product['relationships']['main_image']['data']['id']
    product_image = fetch_image_by_id(auth.token, product_image_id)['data']

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
