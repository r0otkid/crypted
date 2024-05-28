class DefaultContext:
    def __init__(self, user: dict) -> None:
        self.user = user

    async def ctx(self) -> dict:
        return {}