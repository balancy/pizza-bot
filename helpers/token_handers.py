import time

from api.moltin_requests import fetch_auth_token


def get_actual_auth_token(context):
    """Gets actual valid auth token. Returns current token from bot context if
    it's not yet expired, otherwise refreshes it in the context by requesting
    API and returns updated token.

    Args:
        context: bot context

    Returns:
        actual valid auth token
    """

    expires = context.bot_data['token_expires']

    if expires - time.time() > 10:
        return context.bot_data[f'auth_token']

    client_id = context.bot_data['client_id']
    client_secret = context.bot_data['client_secret']

    token_details = fetch_auth_token(client_id, client_secret)

    context.bot_data['token_expires'] = token_details['expires']
    context.bot_data['auth_token'] = token_details['access_token']

    return token_details['access_token']
