import json
import os

from dotenv import load_dotenv
from redis import Redis

from api.moltin_requests import fetch_categories
from helpers.fb_items_formatters import get_formatted_menu
from helpers.token_handers import AuthToken

if __name__ == '__main__':
    load_dotenv()

    redis_host = os.getenv('REDIS_PORT', 'localhost')
    redis_port = os.getenv('REDIS_PORT', 6379)
    db = Redis(host=redis_host, port=redis_port)

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth = AuthToken(client_id, client_secret)

    categories = fetch_categories(auth.token)['data']
    for category in categories:
        slug = category['slug']
        menu = get_formatted_menu(auth, categories, slug)
        db.set(slug, json.dumps(menu))
