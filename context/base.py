class DefaultContext:
    def __init__(self, user: dict) -> None:
        self.user = user

    async def ctx(self) -> dict:
        return {}

class StartContext(DefaultContext):
    async def ctx(self) -> dict:
        return {
            "channel_link": "<a href='https://ya.ru'>канал</a>",
            "chat_link": "<a href='https://ya.ru'>чат</a>",
        }