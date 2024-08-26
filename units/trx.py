from decimal import Decimal
import hashlib
from tronpy import Tron
from tronpy.providers import HTTPProvider
from tronpy.keys import PrivateKey
from database.db import DB
from decorators import timed_cache
from settings.common import CRYPTO_SETTINGS, TRX
from units.base import Unit

class TRXUnit(Unit):
    def __init__(self, network='mainnet'):
        self.crypto = TRX
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

    async def get_network_fee(self) -> float:
        try:
            # Получаем рекомендуемую комиссию за транзакцию
            chain_parameters = self.client.get_chain_parameters()
            for param in chain_parameters:
                if param['key'] == 'getEnergyFee':
                    energy_fee = param['value']
                elif param['key'] == 'getTransactionFee':
                    transaction_fee = param['value']
            
            estimated_size = self.estimate_transaction_size()
            total_fee = transaction_fee + (estimated_size * energy_fee)

            return total_fee / 1e6  # Переводим из Sun в TRX
        except Exception as e:
            print(f"Error fetching network fees: {e}")
            return {}

    @timed_cache(seconds=10)
    async def get_balance(self, address: str) -> float:
        try:
            account_info = self.client.get_account(address)
            balance = account_info.get('balance', 0)
            user = await DB.users.find_one({f'profile.wallet.{TRX}.address': address})
            
            return balance / 1e6 - await self.get_hold(user_id=user['user_id'], crypto=TRX) # Convert from SUN to TRX
        except Exception as e:
            print(f"[{TRX}] Error fetching balance: {e}")
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

    def estimate_transaction_size(self) -> float:
        # Предполагаем размер транзакции в kb
        return 0.25

    def from_satoshis(self, fee_in_sun: int) -> float:
        # 1 TRX = 1,000,000 sun
        return fee_in_sun / 1e6