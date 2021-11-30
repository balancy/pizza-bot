import json
import os

from dotenv import load_dotenv

from api_requests import (
    fetch_auth_token,
    upload_product,
    EntityExistsError,
)

PRODUCTS_FILE = 'menu.json'
ADDRESSES_FILE = 'addresses.json'


def upload_products(auth_token):
    with open(PRODUCTS_FILE, 'r') as products_file:
        products = json.load(products_file)

    for product in products:
        try:
            upload_product(auth_token, product)
        except EntityExistsError:
            print('Product <{}> is already uploaded'.format(product['name']))


if __name__ == '__main__':
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    auth_token = fetch_auth_token(client_id, client_secret)['access_token']

    upload_products(auth_token)
