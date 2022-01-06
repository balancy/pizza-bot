from api.moltin_requests import fetch_categories, fetch_products_by_category_id
from helpers.fb_items_formatters import (
    format_first_menu_element,
    format_last_menu_element,
    format_menu_element,
)


def fetch_front_page_menu(auth_token):
    categories = fetch_categories(auth_token.token)['data']

    first_category = next(
        filter(lambda category: category['slug'] == 'front_page', categories)
    )

    other_categories = list(
        filter(lambda category: category['slug'] != 'front_page', categories)
    )

    products = fetch_products_by_category_id(
        auth_token.token, first_category.get('id')
    )['data']

    products_formatted = [
        format_menu_element(product, auth_token.token) for product in products
    ]

    front_page_menu = [
        format_first_menu_element(),
        *products_formatted,
        format_last_menu_element(other_categories),
    ]

    return front_page_menu
