from abc import ABC, abstractmethod
from decimal import Decimal

from database.db import DB

class Unit(ABC):
    crypto = None

    @abstractmethod
    def validate_address(self, address: str) -> bool:
        pass

    @abstractmethod
    def get_wallet_url(self, address: str) -> str:
        pass

    @abstractmethod
    async def get_balance(self, address: str) -> float:
        pass

    @abstractmethod
    async def get_network_fee(self) -> dict:
        pass

    @abstractmethod
    async def generate_address(self, user_id: int) -> tuple:
        pass

    @abstractmethod
    async def send_coins(self, user: dict, to_address: str, amount: float) -> str:
        pass

    async def has_sufficient_balance(self, address: str, amount: float) -> tuple:
        balance = await self.get_balance(address)
        fee_info = await DB.network_fees.find_one({'crypto': self.crypto})
        network_fee = fee_info['network_fee']
        fee = self.from_satoshis(network_fee * self.estimate_transaction_size())
        return balance >= Decimal(amount) + Decimal(fee), round(Decimal(fee), 5)
    
    async def get_hold(self, user_id: int, crypto: str) -> float:
        user = await DB.users.find_one({'user_id': user_id})
        return float(user['profile']['wallet'][crypto]['hold'])

    @abstractmethod
    def estimate_transaction_size(self) -> int:
        """Estimate transaction size in kilobytes for fee calculation"""
        pass

    @abstractmethod
    def from_satoshis(self, fee_in_satoshis: int) -> float:
        """Convert fee from satoshis (or the smallest unit of the cryptocurrency) to float"""
        pass