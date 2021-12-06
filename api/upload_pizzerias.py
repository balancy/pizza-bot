import json
import os

from dotenv import load_dotenv

from moltin_api_requests import fetch_auth_token, upload_entry

ADDRESSES_FILE = 'addresses.json'
FLOW_SLUG = 'pizzeria'


def upload_pizzerias(auth_token):
    with open(ADDRESSES_FILE, 'r') as addresses_file:
        pizzerias = json.load(addresses_file)

    for pizzeria in pizzerias:
        pizzeria_formatted = {
            'alias': pizzeria['alias'],
            'address': pizzeria['address']['full'],
            'longitude': pizzeria['coordinates']['lon'],
            'latitude': pizzeria['coordinates']['lat'],
        }

        upload_entry(auth_token, pizzeria_formatted, FLOW_SLUG)

        print('Pizzeria <{}> is uploaded'.format(pizzeria['alias']))


if __name__ == '__main__':
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    auth_token = fetch_auth_token(client_id, client_secret)['access_token']

    upload_pizzerias(auth_token)
