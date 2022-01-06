from api.moltin_requests import fetch_categories, fetch_products_by_category_id
from helpers.fb_items_formatters import (
    format_first_menu_element,
    format_last_menu_element,
    format_menu_element,
)


def fetch_menu(auth_token, category_id):
    categories = fetch_categories(auth_token.token)['data']

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

    products = fetch_products_by_category_id(auth_token.token, category_id)[
        'data'
    ]

    products_formatted = [
        format_menu_element(product, auth_token.token) for product in products
    ]

    front_page_menu = [
        format_first_menu_element(),
        *products_formatted,
        format_last_menu_element(other_categories),
    ]

    return front_page_menu
