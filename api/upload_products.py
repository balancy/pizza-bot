import json
import os

from dotenv import load_dotenv

from moltin_api_requests import (
    create_product_image_relation,
    fetch_auth_token,
    upload_image,
    upload_product,
    EntityExistsError,
)

PRODUCTS_FILE = 'menu.json'


def upload_products(auth_token):
    with open(PRODUCTS_FILE, 'r') as products_file:
        products = json.load(products_file)

    for product in products:
        try:
            product_details = upload_product(auth_token, product)
        except EntityExistsError:
            print('Product <{}> is already uploaded'.format(product['name']))
        else:
            image_url = product['product_image']['url']
            image_details = upload_image(auth_token, image_url)

            product_id = product_details['data']['id']
            image_id = image_details['data']['id']
            create_product_image_relation(auth_token, product_id, image_id)

            print('Product <{}> is uploaded'.format(product['name']))


if __name__ == '__main__':
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    auth_token = fetch_auth_token(client_id, client_secret)['access_token']

    upload_products(auth_token)
