class Unit:
    def __init__(self, network='mainnet'):
        self._address = None
        self.network = network

    @property
    def wallet_url(self) -> str:
        return ""

    @staticmethod
    async def generate_address() -> str:
        return ""

    @staticmethod
    async def validate_address(address: str) -> bool:
        return False

    @staticmethod
    async def get_balance(address: str) -> float:
        return 0.0
