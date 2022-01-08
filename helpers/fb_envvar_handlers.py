from enum import Enum
import os

from dotenv import load_dotenv
from redis import Redis

from helpers.token_handers import AuthToken


class State(Enum):
    MENU = 1
    CART = 2


def get_env_vars():
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth = AuthToken(client_id, client_secret)

    redis_host = os.getenv('REDIS_PORT', 'localhost')
    redis_port = os.getenv('REDIS_PORT', 6379)
    db = Redis(host=redis_host, port=redis_port)

    fb_token = os.getenv('PAGE_ACCESS_TOKEN')
    verify_token = os.getenv('VERIFY_TOKEN')
    state = State.MENU

    return auth, db, fb_token, verify_token, state
