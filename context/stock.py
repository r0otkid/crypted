from context.base import DefaultContext


class StockContext(DefaultContext):
    async def ctx(self):
        return {
            'taker_fee': 0,
            'maker_fee': 1,
        }