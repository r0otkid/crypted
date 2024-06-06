import os
from settings.local import *

BOT_TOKEN = os.getenv('CRYPTED_TOKEN')
BASE_PROTO = 'https'
BASE_URL = f'{BASE_PROTO}://{BASE_HOST}'
CRYPTOS = ['BTC', 'TRX', 'TON', 'ETH']