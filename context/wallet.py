from context.base import DefaultContext
from database.state import set_state


class WalletContext(DefaultContext):
    async def ctx(self):
        return {
            'btc_balance': 0.005,
            'wallet_currency': 'RUB',
            'total_balance': 1000,
        }


class ReplenishContext(DefaultContext):
    async def ctx(self):
        return {
            'address': 'dfjkngdfng45jg45jgcvkmvdf',
        }

class WithdrawContext(DefaultContext):
    async def ctx(self):
        return {
            'crypto': 'BTC',
        }