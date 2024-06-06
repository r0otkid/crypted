import hashlib
from eth_account import Account
from web3 import Web3
from settings.common import CRYPTO_SETTINGS

INFURA_PROJECT_ID = CRYPTO_SETTINGS['ETH']['api_key']

class ETHUnit:
    def __init__(self, network='mainnet'):
        self._address = None
        self.network = network
        if self.network == 'mainnet':
            self.web3 = Web3(Web3.HTTPProvider(f'https://mainnet.infura.io/v3/{INFURA_PROJECT_ID}'))
        elif self.network == 'testnet':
            self.web3 = Web3(Web3.HTTPProvider(f'https://goerli.infura.io/v3/{INFURA_PROJECT_ID}'))
        elif self.network == 'sepolia':
            self.web3 = Web3(Web3.HTTPProvider(f'https://sepolia.infura.io/v3/{INFURA_PROJECT_ID}'))
        else:
            raise ValueError(f'Unsupported network: {self.network}')

    @property
    def wallet_url(self) -> str:
        if self._address:
            if self.network == 'mainnet':
                return f'https://etherscan.io/address/{self._address}'
            elif self.network == 'testnet':
                return f'https://goerli.etherscan.io/address/{self._address}'
            elif self.network == 'sepolia':
                return f'https://sepolia.etherscan.io/address/{self._address}'
        return None

    async def generate_address(self, user_id) -> tuple:
        # Generate private key from user_id
        private_key = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()
        
        self._address = self.web3
        pa = self.web3.eth.account.from_key(private_key)
        self._address = pa.address
        return self._address, private_key

    @staticmethod
    def validate_address(address: str) -> bool:
        return Web3.is_address(address)

    async def get_balance(self, address: str) -> float:
        try:
            balance_wei = self.web3.eth.get_balance(address)
            balance_eth = self.web3.from_wei(balance_wei, 'ether')
            return balance_eth
        except Exception as e:
            print(f"Error fetching balance: {e}")
            return 0.0

    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        # Convert the amount from ETH to Wei
        amount_wei = self.web3.to_wei(amount, 'ether')

        # Generate private key from user_id
        private_key = hashlib.sha256(user['user_id'].encode('utf-8')).hexdigest()

        try:
            # Create account
            account = Account.from_key(private_key)

            # Build transaction
            tx = {
                'nonce': self.web3.eth.get_transaction_count(user['profile']['wallet']['TON']['address']),
                'to': to_address,
                'value': amount_wei,
                'gas': 2000000,
                'gasPrice': self.web3.to_wei('50', 'gwei')
            }

            # Sign transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, private_key)

            # Send transaction
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            return self.web3.to_hex(tx_hash)
        except Exception as e:
            print(f"Error sending coins: {e}")
            return None