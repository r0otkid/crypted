import logging
from settings.common import CRYPTO_SETTINGS
import re
import aiohttp
from bip32utils import BIP32Key
from mnemonic import Mnemonic
import hashlib
from binascii import unhexlify
from hashlib import sha512
from typing import Optional, Tuple

MAINNET_URL = "https://toncenter.com"
TESTNET_URL = "https://testnet.toncenter.com"

class TONUnit:
    def __init__(self, network='mainnet', access_key: Optional[str] = None):
        self._address = None
        self.network = network
        self.access_key = access_key
        self.mnemo = Mnemonic("english")

        if network == 'mainnet':
            self.base_url = MAINNET_URL
        elif network == 'testnet':
            self.base_url = TESTNET_URL
        else:
            raise ValueError("Invalid network. Choose 'mainnet' or 'testnet'.")

    @property
    def wallet_url(self) -> str:
        if self._address:
            if self.network == 'mainnet':
                return f'https://tonscan.org/address/{self._address}'
            elif self.network == 'testnet':
                return f'https://nile.tonscan.org/address/{self._address}'
        return None

    async def generate_address(self, user_id: int) -> Tuple[str, str]:
        mnemonic_phrase = self._generate_mnemonic(user_id)
        key_pair = self._derive_sign_keys(mnemonic_phrase)
        self._address = self._get_address_from_public_key(key_pair['public'])
        return self._address, key_pair['secret']

    def _mnemonic_from_entropy(self, entropy: bytes) -> str:
        return self.mnemo.to_mnemonic(entropy)

    def _derive_sign_keys(self, phrase: str) -> dict:
        seed = self.mnemo.to_seed(phrase)
        master_key = BIP32Key.fromEntropy(seed)
        return {
            'public': master_key.PublicKey().hex(),
            'secret': master_key.WalletImportFormat()
        }

    def _generate_mnemonic(self, user_id: int) -> str:
        user_id_str = str(user_id)
        entropy = hashlib.sha256(user_id_str.encode()).digest()[:32]  # Используем 32 байта энтропии
        return self._mnemonic_from_entropy(entropy)

    def _get_address_from_public_key(self, public_key: str) -> str:
        # Convert the public key to bytes
        public_key_bytes = unhexlify(public_key)

        # Calculate the SHA-512 hash of the public key
        hash = sha512(public_key_bytes).digest()

        # The address is the first 32 bytes of the hash, encoded as hex
        address = hash[:32].hex()

        # Add the "0:" prefix
        return "0:" + address
    
    async def get_balance(self, address: str) -> float:
        base_url = f"{self.base_url}/api/v2/getAddressBalance"
        params = f"?address={address}&api_key={CRYPTO_SETTINGS['TON']['api_key']}"
        url = base_url + params

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url) as response:
                    data = await response.json()
                    print(data)
                    if 'result' in data and data['ok']:
                        return float(data['result']) / 10**9
                    else:
                        raise ValueError("Invalid response: 'balance' not found")
            except Exception as e:
                logging.error(f"Error retrieving balance: {e}")
                return 0.0

    @staticmethod
    def validate_address(address: str) -> bool:
        try:
            # TON addresses usually start with "0:" followed by a 64-character hash
            match = re.fullmatch(r"0:[a-fA-F0-9]{64}", address)
            return match is not None
        except Exception:
            return False

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        try:
            amount_nanoton = int(amount * 1e9)
            key_pair = self._derive_sign_keys(self._generate_mnemonic(user['user_id']))

            txn = {
                'from': user['profile']['wallet']['TON']['address'],
                'to': to_address,
                'value': amount_nanoton,
                'private_key': key_pair['secret'],
                'public_key': key_pair['public']
            }

            url = f'{self.base_urls[0]}/transactions'
            headers = {'Authorization': f'Bearer {self.access_key}'} if self.access_key else {}

            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=txn, headers=headers) as response:
                    response.raise_for_status()
                    txn_info = await response.json()
                    return txn_info['id']
        except Exception as e:
            logging.error(f"Error sending coins: {e}")
            return None
