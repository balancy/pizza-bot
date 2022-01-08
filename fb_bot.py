from datetime import datetime

from flask import Flask, request
from flask_apscheduler import APScheduler

from helpers.fb_envvar_handlers import get_env_vars
from helpers.fb_action_handlers import handle_menu_caching, handle_user_input

AUTH, DB, FB_TOKEN, VERIFY_TOKEN, state = get_env_vars()


class Config:
    SCHEDULER_API_ENABLED = True
    SCHEDULER_TIMEZONE = "Europe/Paris"


app = Flask(__name__)
app.config.from_object(Config())

scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()


@scheduler.task('interval', minutes=1, next_run_time=datetime.now())
def cache_menu():
    handle_menu_caching(AUTH, DB)
    print('cached')


@app.route('/', methods=['GET'])
def verify():
    """Verifies webhook for FB."""

    args = request.args
    if args.get('hub.mode') == 'subscribe' and args.get('hub.challenge'):
        if not request.args.get('hub.verify_token') == VERIFY_TOKEN:
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
                    state = handle_user_input(
                        DB, state, user_id, AUTH, FB_TOKEN, message, payload
                    )

    return "ok", 200
