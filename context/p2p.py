from context.base import DefaultContext


class P2PContext(DefaultContext):
    async def ctx(self):
        return {
            'buy_fee': 0,
            'sell_fee': 1,
        }