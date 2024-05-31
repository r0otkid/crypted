import os
from settings.local import BASE_HOST, CRYPTO_SETTINGS

BOT_TOKEN = os.getenv('CRYPTED_TOKEN')
BASE_PROTO = 'https'
BASE_URL = f'{BASE_PROTO}://{BASE_HOST}'