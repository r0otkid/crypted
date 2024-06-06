import hashlib
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from settings.common import CRYPTO_SETTINGS

class TRXUnit:
    def __init__(self, network='mainnet'):
        self._address = None
        self.network = network
        endpoint_uri = 'https://api.shasta.trongrid.io' if network == 'testnet' else 'https://api.trongrid.io'
        provider = HTTPProvider(
            api_key=CRYPTO_SETTINGS['TRX']['api_key'], endpoint_uri=endpoint_uri
        )
        self.client = Tron(network=network, provider=provider)

    @property
    def wallet_url(self) -> str:
        if self._address:
            if self.network == 'mainnet':
                return f'https://tronscan.org/#/address/{self._address}'
            elif self.network == 'testnet':
                return f'https://nile.tronscan.org/#/address/{self._address}'
        return None

    async def generate_address(self, user_id: int) -> tuple:
        # Generate private key from user_id
        private_key_hex = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()
        private_key = PrivateKey.fromhex(private_key_hex)
        self._address = private_key.public_key.to_base58check_address()
        return self._address, private_key

    @staticmethod
    def validate_address(address: str) -> bool:
        # Validate TRX address
        try:
            Tron.decode_check_address(address)
            return True
        except Exception:
            return False

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
        amount_sun = int(amount * 1e6)

        # Generate private key from user_id
        private_key_hex = hashlib.sha256(user['user_id'].encode('utf-8')).hexdigest()
        private_key = PrivateKey.fromhex(private_key_hex)

        try:
            # Create and sign transaction
            txn = (
                self.client.trx.transfer(user['profile']['wallet']['TON']['address'], to_address, amount_sun)
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
