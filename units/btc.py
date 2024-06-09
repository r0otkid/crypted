from decimal import Decimal
import logging
from typing import Optional
from bitmerchant.wallet import Wallet
from bitmerchant.network import BitcoinMainNet, BitcoinTestNet
import blockcypher
from database.db import DB
from settings.common import CRYPTO_SETTINGS, BTC, ROOT_ID
from units.base import Unit
import hashlib
import base58

from decorators import timed_cache



class BTCUnit(Unit):
    def __init__(self, network='mainnet'):
        self.network = network
        self.symbol = 'bcy' if self.network == 'testnet' else 'btc'
        self.api_token = CRYPTO_SETTINGS[BTC]['api_key']
    
    def _add_faucet_coins(self, address):
        faucet_tx = blockcypher.send_faucet_coins(
            address_to_fund=address, satoshis=1000000, coin_symbol=self.symbol, api_key=self.api_token
        )
        logging.info("Faucet txid is", faucet_tx['tx_ref'])

    async def _get_master_key(self):
        master_user = await DB.users.find_one({'user_id': ROOT_ID})
        return master_user['profile']['wallet'][BTC]['private_key']

    def get_wallet_url(self, address) -> str:
        if self.network == 'mainnet':
            return f'https://live.blockcypher.com/{self.symbol}/address/{address}/'
        elif self.network == 'testnet':
            return f'https://live.blockcypher.com/{self.symbol}/address/{address}/'
        return ''
    
    async def generate_address(self, user_id: int) -> tuple:
        if user_id == ROOT_ID:
            keypair = blockcypher.generate_new_address(coin_symbol=self.symbol, api_key=self.api_token)
            public_address = keypair['address']
            private_key = keypair['private']
            self._add_faucet_coins(address=public_address)
        else:
            network = BitcoinTestNet if self.network == 'testnet' else BitcoinMainNet
            master_key = self._get_master_key()
            master_wallet = Wallet.from_master_secret(master_key, network=network)
            user_wallet = master_wallet.get_child(user_id, is_prime=True)
            public_address = user_wallet.to_address()
            private_key = user_wallet.export_to_wif()
        return public_address, private_key

    def validate_address(self, address: str) -> bool:
        try:
            if not blockcypher.api.is_valid_address_for_coinsymbol(address, coin_symbol=self.symbol):
                raise ValueError(f"Invalid address ")

            # Decode the address using base58
            decoded_address = base58.b58decode(address)

            # The address should be 25 bytes long (1 byte network + 20 bytes hash + 4 bytes checksum)
            if len(decoded_address) != 25:
                return False

            # Separate the checksum and the address
            network_byte_and_hash = decoded_address[:-4]
            checksum = decoded_address[-4:]

            # Perform SHA-256 hash twice
            sha256_1 = hashlib.sha256(network_byte_and_hash).digest()
            sha256_2 = hashlib.sha256(sha256_1).digest()

            # Validate the checksum
            if sha256_2[:4] == checksum:
                return True
            else:
                return False
        except Exception as e:
            # If any exception occurs during decoding or hashing, the address is invalid
            return False

    @timed_cache(seconds=30)
    async def get_balance(self, address: str) -> Optional[float]:
        # self._add_faucet_coins(address=address)
        try:
            address_overview = blockcypher.get_address_overview(
                address=address,
                coin_symbol=self.symbol,
                api_key=self.api_token
            )
            balance =  address_overview['balance'] / Decimal(1e8)
            return float(balance)
        
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return None

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        # Convert the amount from BTC to satoshis
        amount_satoshi = int(amount * Decimal(1e8))
        tx_ref = blockcypher.simple_spend(
            from_privkey=user['profile']['wallet'][BTC]['private_key'],
            to_address=to_address,
            to_satoshis=amount_satoshi,
            coin_symbol=self.symbol,
            api_key=self.api_token,
        )
        print("Txid is", tx_ref)
        return tx_ref
