from base64 import b64encode
import base64
from decimal import Decimal
import json
import logging
import time
from traceback import print_tb

from decorators import timed_cache
from settings.common import CRYPTO_SETTINGS, TON
import re
import aiohttp
import nacl.signing
from nacl.encoding import HexEncoder

from mnemonic import Mnemonic
import hashlib
from binascii import unhexlify
from hashlib import sha512
from typing import Optional, Tuple

MAINNET_URL = "https://toncenter.com"
TESTNET_URL = "https://testnet.toncenter.com"

class TONUnit:
    def __init__(self, network='mainnet', access_key: Optional[str] = None):
        self.network = network
        self.access_key = access_key
        self.mnemo = Mnemonic("english")

        if network == 'mainnet':
            self.base_url = MAINNET_URL
        elif network == 'testnet':
            self.base_url = TESTNET_URL
        else:
            raise ValueError("Invalid network. Choose 'mainnet' or 'testnet'.")

    def get_wallet_url(self, address) -> str:
        if self.network == 'mainnet':
            return f'https://tonscan.org/address/{address}'
        elif self.network == 'testnet':
            return f'https://testnet.tonscan.org/address/{address}'
        return ''

    async def generate_address(self, user_id: int) -> Tuple[str, str]:
        mnemonic_phrase = self._generate_mnemonic(user_id)
        key_pair = self._derive_sign_keys(mnemonic_phrase)
        return self._get_address_from_public_key(key_pair['public']), key_pair['secret']

    def _mnemonic_from_entropy(self, entropy: bytes) -> str:
        return self.mnemo.to_mnemonic(entropy)

    def _derive_sign_keys(self, phrase: str) -> dict:
        # Преобразуем фразу в байтовый формат и получаем хэш
        phrase_bytes = phrase.encode()
        seed = hashlib.sha256(phrase_bytes).digest()

        # Используем хэш для генерации ключей
        signing_key = nacl.signing.SigningKey(seed=seed)

        # Получаем открытый и закрытый ключи
        verify_key = signing_key.verify_key
        public_key_hex = verify_key.encode(encoder=HexEncoder).decode()
        signing_key_hex = signing_key.encode(encoder=HexEncoder).decode()

        return {
            'public': public_key_hex,
            'secret': signing_key_hex
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
    
    @timed_cache(seconds=10)
    async def get_balance(self, address: str) -> float:
        base_url = f"{self.base_url}/api/v2/getAddressBalance"
        params = f"?address={address}&api_key={CRYPTO_SETTINGS[TON]['api_key']}"
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
        return True
        try:
            # TON addresses usually start with "0:" followed by a 64-character hash
            match = re.fullmatch(r"0:[a-fA-F0-9]{64}", address)
            return match is not None
        except Exception:
            return False

    @staticmethod
    def sign_transaction(transaction_json: str, private_key: str) -> str:
        # Парсим JSON транзакции
        transaction_dict = json.loads(transaction_json)

        # Сериализуем транзакцию без поля "signature"
        transaction_without_signature = json.dumps({k: v for k, v in transaction_dict.items() if k != 'signature'}, sort_keys=True)

        # Преобразуем приватный ключ в байты
        private_key_bytes = bytes.fromhex(private_key)

        # Создаем экземпляр объекта для работы с приватным ключом Ed25519
        signing_key = nacl.signing.SigningKey(private_key_bytes)

        # Создаем подпись транзакции
        signature = signing_key.sign(transaction_without_signature.encode('utf-8'))

        # Кодируем подпись в base64
        signature_base64 = b64encode(signature.signature).decode('utf-8')

        return signature_base64

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        pass
