from context.base import DefaultContext


class WalletContext(DefaultContext):
    async def ctx(self):
        return {
            'btc_balance': 0.005,
            'wallet_currency': 'RUB',
            'total_balance': 1000,
        }