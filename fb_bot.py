from datetime import datetime
from enum import Enum
import os

from dotenv import load_dotenv
from flask import Flask, request
from flask_apscheduler import APScheduler
from redis import Redis

from helpers.fb_action_handlers import (
    handle_menu_caching,
    handle_user_input,
    State,
)
from helpers.token_handers import AuthToken


class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Europe/Paris"


class MyFlaskApp(Flask):
    load_dotenv()

    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth = AuthToken(client_id, client_secret)

    redis_password = os.getenv('REDIS_PASSWORD', '')
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = os.getenv('REDIS_PORT', 6379)
    db = Redis(host=redis_host, port=redis_port, password=redis_password)

    fb_token = os.getenv('PAGE_ACCESS_TOKEN')
    verify_token = os.getenv('VERIFY_TOKEN')
    state = State.MENU


app = MyFlaskApp(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@scheduler.task('interval', minutes=1, next_run_time=datetime.now())
def cache_menu():
    handle_menu_caching(app.auth, app.db)


@app.route('/', methods=['GET'])
def verify():
    """Verifies webhook for FB."""

    args = request.args
    if args.get('hub.mode') == 'subscribe' and args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == app.verify_token:
            return 'Verification token mismatch', 403
        return request.args['hub.challenge'], 200

    return 'Hello world', 200


@app.route('/', methods=['POST'])
def webhook():
    """Webhook to handle facebook messages."""

    data = request.get_json()
    global state

    if data['object'] == 'page':
        for entry in data['entry']:
            for event in entry['messaging']:
                user_id = event['sender']['id']

                message = event.get('message')
                postback = event.get('postback')

                if message or postback:
                    message = message['text'] if message else None
                    payload = postback['payload'] if postback else None
                    app.state = handle_user_input(
                        db=app.db,
                        state=app.state,
                        user_id=user_id,
                        auth=app.auth,
                        fb_token=app.fb_token,
                        message=message,
                        payload=payload,
                    )

    return "ok", 200
