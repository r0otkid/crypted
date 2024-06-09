import hashlib
# from eth_account import Account
from web3 import Web3
from decorators import timed_cache
from settings.common import CRYPTO_SETTINGS, ETH


class ETHUnit:
    NETWORKS = {
        'mainnet': 'mainnet.infura.io/v3',
        'testnet': 'goerli.infura.io/v3',
        'sepolia': 'sepolia.infura.io/v3'
    }

    EXPLORER_URLS = {
        'mainnet': 'https://etherscan.io/address',
        'testnet': 'https://goerli.etherscan.io/address',
        'sepolia': 'https://sepolia.etherscan.io/address'
    }

    def __init__(self, network='mainnet'):
        if network not in self.NETWORKS:
            raise ValueError(f'Unsupported network: {network}')

        self.network = network
        self.web3 = Web3(Web3.HTTPProvider(f'https://{self.NETWORKS[self.network]}/{CRYPTO_SETTINGS[ETH]['api_key']}'))

    def get_wallet_url(self, address) -> str:
        return f"{self.EXPLORER_URLS.get(self.network, '')}/{address}"

    async def generate_address(self, user_id) -> tuple:
        # Generate private key from user_id
        private_key = hashlib.sha256(str(user_id).encode('utf-8')).hexdigest()
        
        pa = self.web3.eth.account.from_key(private_key)
        return  pa.address, private_key

    @staticmethod
    def validate_address(address: str) -> bool:
        return Web3.is_address(address)

    @timed_cache(seconds=30)
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
            # account = Account.from_key(private_key)

            # Build transaction
            tx = {
                'nonce': self.web3.eth.get_transaction_count(user['profile']['wallet'][ETH]['address']),
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
