import json
from textwrap import dedent

import requests
from slugify import slugify

API_ROOT = 'https://api.moltin.com'


class EntityExistsError(requests.models.HTTPError):
    pass


def fetch_auth_token(client_id, client_secret=None):
    """Make an API request to fetch bearer token

    Args:
        client_id: elasticpath client id

    Returns:
        API response containing authorization token
    """

    if client_secret:
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials',
        }
    else:
        data = {
            'client_id': client_id,
            'grant_type': 'implicit',
        }

    response = requests.post(
        f'{API_ROOT}/oauth/access_token',
        data=data,
    )
    response.raise_for_status()

    return response.json()


def format_product_details(product_details):
    """Format product details from json file to format requesting by API.

    Args:
        product_details: product details dictionary

    Returns:
        formatted product data for API
    """
    slugified_name = slugify(product_details['name'])
    description = dedent(
        '''\
            {}

            Пищевая ценность:
            Жиры: {}
            Протеины: {}
            Углеводы: {}
            Ккал: {}
            Вес: {}
        '''.format(
            product_details['description'],
            (food_value := product_details['food_value'])['fats'],
            food_value['proteins'],
            food_value['carbohydrates'],
            food_value['kiloCalories'],
            food_value['weight'],
        )
    )

    data = {
        'data': {
            'type': 'product',
            'name': product_details['name'],
            'slug': slugified_name,
            'sku': '{}-{}'.format(slugified_name, product_details['id']),
            'description': description,
            'manage_stock': False,
            'price': [
                {
                    'amount': product_details['price'],
                    'currency': 'RUB',
                    'includes_tax': True,
                }
            ],
            'status': 'live',
            'commodity_type': 'physical',
        },
    }

    return data


def upload_product(token, product_details):
    """Make an API request to add product to cart

    Args:
        token: authorization token
        cart_name: name of cart to add product to
        product_id: id of product to add to cart
        quantity: quantity of product to add to cart

    Returns:
        API response containing all cart items
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = format_product_details(product_details)

    response = requests.post(
        f'{API_ROOT}/v2/products',
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 409:
        raise EntityExistsError
    response.raise_for_status()

    return response.json()


def upload_image(token, image_url):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    files = {'file_location': (None, image_url)}

    response = requests.post(
        f'{API_ROOT}/v2/files',
        headers=headers,
        files=files,
    )

    if response.status_code == 409:
        raise EntityExistsError
    response.raise_for_status()

    return response.json()


def create_product_image_relation(token, product_id, image_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'type': 'main_image',
            'id': image_id,
        },
    }

    response = requests.post(
        f'{API_ROOT}/v2/products/{product_id}/relationships/main-image',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


def create_flow(token, name, description):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        "data": {
            "type": "flow",
            "name": name,
            "slug": slugify(name),
            "description": description,
            "enabled": True,
        }
    }

    response = requests.post(
        f'{API_ROOT}/v2/flows',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


def create_flow_field(token, name, description, field_type, flow_id):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'type': 'field',
            'name': name,
            'slug': slugify(name),
            'field_type': field_type,
            'description': description,
            'required': True,
            'enabled': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    }
                }
            },
        }
    }

    response = requests.post(
        f'{API_ROOT}/v2/fields',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


def upload_entry(token, flow_data, flow_slug):
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'type': 'entry',
            **flow_data,
        }
    }

    response = requests.post(
        f'{API_ROOT}/v2/flows/{flow_slug}/entries',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


def fetch_products(token):
    """Make an API request to fetch all products in catalog

    Args:
        token: authorization token

    Returns:
        API response containing products
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        'https://api.moltin.com/v2/products',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_product_by_id(token, product_id):
    """Make an API request to fetch product details

    Args:
        token: authorization token
        product_id: id of product to fetch details of

    Returns:
        API response containing product details
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/products/{product_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def fetch_image_by_id(token, image_id):
    """Make an API request to fetch image

    Args:
        token: authorization token
        image_id: id of image to fetch

    Returns:
        API response containing image url
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/files/{image_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def add_product_to_cart(token, cart_name, product_id, quantity):
    """Make an API request to add product to cart

    Args:
        token: authorization token
        cart_name: name of cart to add product to
        product_id: id of product to add to cart
        quantity: quantity of product to add to cart

    Returns:
        API response containing all cart items
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity,
        }
    }

    response = requests.post(
        f'https://api.moltin.com/v2/carts/{cart_name}/items',
        headers=headers,
        data=json.dumps(data),
    )
    response.raise_for_status()

    return response.json()


def fetch_cart_items(token, cart_name):
    """Make an API request to fetch all cart items

    Args:
        token: authorization token
        cart_name: name of cart to fetch items from

    Returns:
        API response containing all cart items
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.get(
        f'https://api.moltin.com/v2/carts/{cart_name}/items', headers=headers
    )
    response.raise_for_status()

    return response.json()


def remove_cart_item_by_id(token, cart_name, item_id):
    """Make an API request to remove item from cart

    Args:
        token: authorization token
        cart_name: name of cart to remove item from
        item_id: id of item to remove from cart

    Returns:
        API response containing all cart items
    """
    headers = {'Authorization': f'Bearer {token}'}

    response = requests.delete(
        f'https://api.moltin.com/v2/carts/{cart_name}/items/{item_id}',
        headers=headers,
    )
    response.raise_for_status()

    return response.json()


def create_customer(token, email):
    """Make an API request to create customer

    Args:
        token: authorization token
        email: customer email to use during creating

    Returns:
        API response containing customer details
    """
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    data = {
        'data': {
            'type': 'customer',
            'name': 'name',
            'email': email,
            'password': 'password',
        }
    }

    response = requests.post(
        'https://api.moltin.com/v2/customers',
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 409:
        raise EntityExistsError

    response.raise_for_status()

    return response.json()
