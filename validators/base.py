from database.state import States, set_state
from triggers import get_all_triggers


class DefaultValidator():
    def __init__(self, context) -> None:
        self.context = context

    async def clear_chain(self, selected: list):
        # удаляем не прошедший триггер из цепочки
        if selected[-1] not in get_all_triggers(self.context.triggers):
            await set_state(self.context.user['user_id'], States.SELECTED, selected[:-1])

    async def update_chain(self, selected: list, value: str):
        await set_state(self.context.user['user_id'], States.SELECTED, selected[:-1] + [str(value)])

    async def validate(self, value: str) -> str:
        return f'Can validate: {value}'