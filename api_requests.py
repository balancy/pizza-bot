import json

import requests
from slugify import slugify


class EntityExistsError(requests.models.HTTPError):
    pass


def fetch_auth_token(client_id, client_secret):
    """Make an API request to fetch bearer token

    Args:
        client_id: elasticpath client id

    Returns:
        API response containing authorization token
    """
    data = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials',
    }

    response = requests.post(
        'https://api.moltin.com/oauth/access_token',
        data=data,
    )
    response.raise_for_status()

    return response.json()


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

    slugified_name = slugify(product_details['name'])

    data = {
        'data': {
            'type': 'product',
            'name': product_details['name'],
            'slug': slugified_name,
            'sku': '{}-{}'.format(slugified_name, product_details['id']),
            'description': product_details['description'],
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

    response = requests.post(
        'https://api.moltin.com/v2/products',
        headers=headers,
        data=json.dumps(data),
    )

    if response.status_code == 409:
        raise EntityExistsError
    response.raise_for_status()

    image_url = product_details['product_image']['url']
    upload_image(token, image_url)

    return response.json()


def upload_image(token, image_url):
    headers = {
        'Authorization': f'Bearer {token}',
    }

    files = {'file_location': (None, image_url)}

    response = requests.post(
        'https://api.moltin.com/v2/files',
        headers=headers,
        files=files,
    )

    if response.status_code == 409:
        raise EntityExistsError
    response.raise_for_status()

    return response.json()
