import os
from settings.local import *

BOT_TOKEN = os.getenv('CRYPTED_TOKEN')
BASE_PROTO = 'https'
BASE_URL = f'{BASE_PROTO}://{BASE_HOST}'
CRYPTOS = ['BTC', 'TRX', 'TON', 'ETH']
BTC = CRYPTOS[0]
TRX = CRYPTOS[1]
TON = CRYPTOS[2]
ETH = CRYPTOS[3]

CRYPTO_SETTINGS = {
    BTC: {
        "network": "testnet",
        "api_key": os.getenv('BLOCKCYPHER_API_KEY'),
    },
    TRX: {
        "network": "testnet",
        "api_key": os.getenv('TRONGRID_API_KEY'),
    },
    TON: {
        "network": "testnet",
        "api_key": os.getenv('TON_API_KEY'),
    },
    ETH: {
        "network": "sepolia",  # or testnet for Goerli
        "api_key": os.getenv('INFURA_PROJECT_ID')
    }
}

# rates
CRYPTO_COMPARE_API_KEY = os.getenv('CRYPTO_COMPARE_API_KEY')