import aiohttp
from units.base import Unit
import hashlib
import base58
from ecdsa import SigningKey, SECP256k1


class BTCUnit(Unit):
    def __init__(self, network='mainnet'):
        self._address = None
        self.network = network

    @property
    def wallet_url(self) -> str:
        if self._address:
            if self.network == 'mainnet':
                return f'https://live.blockcypher.com/btc/address/{self._address}/'
            elif self.network == 'testnet':
                return f'https://live.blockcypher.com/btc-testnet/address/{self._address}/'
        return None

    async def generate_address(self, user_id: int) -> tuple:
        # Step 1: Create a private key using user_id as the seed
        private_key = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()

        # Step 2: Generate public key
        sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        vk = sk.verifying_key
        public_key = b'\x04' + vk.to_string()

        # Step 3: SHA-256 hash of the public key
        sha256_public_key = hashlib.sha256(public_key).digest()

        # Step 4: RIPEMD-160 hash of the SHA-256
        ripemd160 = hashlib.new('ripemd160')
        ripemd160.update(sha256_public_key)
        hashed_public_key = ripemd160.digest()

        # Step 5: Add network byte (0x00 for Bitcoin Mainnet, 0x6F for Testnet)
        if self.network == 'mainnet':
            network_byte = b'\x00' + hashed_public_key
        elif self.network == 'testnet':
            network_byte = b'\x6F' + hashed_public_key

        # Step 6: SHA-256 hash of the extended RIPEMD-160 result
        sha256_network = hashlib.sha256(network_byte).digest()

        # Step 7: SHA-256 hash of the result of the previous SHA-256 hash
        sha256_network_2 = hashlib.sha256(sha256_network).digest()

        # Step 8: Take the first 4 bytes of the second SHA-256 hash; this is the checksum
        checksum = sha256_network_2[:4]

        # Step 9: Add the 4 checksum bytes from step 8 at the end of extended RIPEMD-160 hash from step 5
        binary_address = network_byte + checksum

        # Step 10: Convert the result from a byte string into a base58 string using Base58Check encoding
        bitcoin_address = base58.b58encode(binary_address)

        self._address = bitcoin_address.decode('utf-8')
        return self._address, private_key

    @staticmethod
    def validate_address(address: str) -> bool:
        try:
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

    async def get_balance(self, address: str) -> float:
        # URL для запроса к API Blockcypher
        if self.network == 'mainnet':
            url = f'https://api.blockcypher.com/v1/btc/main/addrs/{address}/balance'
        elif self.network == 'testnet':
            url = f'https://api.blockcypher.com/v1/btc/test3/addrs/{address}/balance'

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    # Проверка успешности запроса
                    response.raise_for_status()
                    # Получение данных в формате JSON
                    data = await response.json()
                    # Баланс в сатоши, конвертируем в биткоины
                    balance_satoshi = data.get('balance', 0)
                    balance_btc = balance_satoshi / 1e8
                    return balance_btc
        except aiohttp.ClientError as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        # Convert the amount from BTC to satoshis
        amount_satoshi = int(amount * 1e8)

        # URL для API Blockcypher
        if self.network == 'mainnet':
            base_url = 'https://api.blockcypher.com/v1/btc/main'
        elif self.network == 'testnet':
            base_url = 'https://api.blockcypher.com/v1/btc/test3'

        # Generate private key from user_id
        private_key_hex = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        private_key = SigningKey.from_string(bytes.fromhex(private_key_hex), curve=SECP256k1)

        try:
            # Step 1: Create a new transaction skeleton
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f'{base_url}/txs/new',
                    json={
                        'inputs': [{'addresses': [user['profile']['wallet']['TON']['address']]}],
                        'outputs': [{'addresses': [to_address], 'value': amount_satoshi}],
                    },
                ) as response:
                    response.raise_for_status()
                    tx_skeleton = await response.json()

            # Step 2: Sign each of the transaction's inputs
            for tx_input in tx_skeleton['tosign']:
                signature = private_key.sign(bytes.fromhex(tx_input))
                tx_skeleton['signatures'].append(signature.hex())
                tx_skeleton['pubkeys'].append(private_key.verifying_key.to_string().hex())

            # Step 3: Send the signed transaction
            async with aiohttp.ClientSession() as session:
                async with session.post(f'{base_url}/txs/send', json=tx_skeleton) as response:
                    response.raise_for_status()
                    tx = await response.json()

            return tx['tx']['hash']
        except aiohttp.ClientError as e:
            print(f"Error sending coins: {e}")
            return None
