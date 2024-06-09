from decimal import Decimal
import hashlib
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from decorators import timed_cache
from settings.common import CRYPTO_SETTINGS, TRX

class TRXUnit:
    def __init__(self, network='mainnet'):
        self.network = network
        endpoint_uri = 'https://api.shasta.trongrid.io' if network == 'testnet' else 'https://api.trongrid.io'
        provider = HTTPProvider(
            api_key=CRYPTO_SETTINGS[TRX]['api_key'], endpoint_uri=endpoint_uri
        )
        self.client = Tron(network=network, provider=provider)

    def get_wallet_url(self, address) -> str:
        if self.network == 'mainnet':
            return f'https://tronscan.org/#/address/{address}'
        elif self.network == 'testnet':
            return f'https://shasta.tronscan.org/#/address/{address}'
        return ''

    async def generate_address(self, user_id: int) -> tuple:
        # Generate private key from user_id
        private_key_hex = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()
        private_key = PrivateKey.fromhex(private_key_hex)
        return private_key.public_key.to_base58check_address(), private_key

    @staticmethod
    def validate_address(address: str) -> bool:
        try:
            return Tron.is_address(address)
        except Exception:
            return False

    @timed_cache(seconds=10)
    async def get_balance(self, address: str) -> float:
        try:
            account_info = self.client.get_account(address)
            balance = account_info.get('balance', 0)
            return balance / 1e6  # Convert from SUN to TRX
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        # Convert the amount from TRX to SUN
        amount_sun = int(amount * Decimal(1e6))

        # Generate private key from user_id
        private_key_hex = hashlib.sha256(str(user['user_id']).encode('utf-8')).hexdigest()
        private_key = PrivateKey.fromhex(private_key_hex)

        try:
            # Create and sign transaction
            txn = (
                self.client.trx.transfer(user['profile']['wallet'][TRX]['address'], to_address, amount_sun)
                .memo("TRX transfer")
                .build()
                .sign(private_key)
            )

            # Broadcast transaction
            result = self.client.broadcast(txn)

            return result['txid']
        except Exception as e:
            print(f"Error sending coins: {e}")
            return None
