import json
import os

from dotenv import load_dotenv

from api_requests import fetch_auth_token, upload_product


if __name__ == '__main__':
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')

    auth_token = fetch_auth_token(client_id, client_secret)['access_token']

    with open("menu.json", "r") as menu_file:
        menu = json.load(menu_file)

    for menu_item in menu:
        upload_product(auth_token, menu_item)
