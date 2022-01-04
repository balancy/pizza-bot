import time

from api.moltin_requests import fetch_auth_token


class AuthToken:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token_expires = time.time()
        self.auth_token = ''

    @property
    def token(self):
        if self.token_expires - time.time() > 10:
            return self.auth_token

        self.__refresh_token()

        return self.auth_token

    def __refresh_token(self):
        token_details = fetch_auth_token(self.client_id, self.client_secret)
        self.token_expires = token_details['expires']
        self.auth_token = token_details['access_token']
