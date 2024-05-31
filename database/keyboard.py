from database.db import DB
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.state import States, get_state, set_state

async def get_keyboard(keyboard_id: str, user: dict) -> InlineKeyboardMarkup:
    selected = await get_state(user_id=user['user_id'], key=States.SELECTED)
    keyboard_data = await DB.keyboards.find_one({'keyboard_id': keyboard_id})
    if not keyboard_data:
        return None
    
    keyboard_buttons = []
    for row in keyboard_data['buttons']:
        keyboard_buttons.append([InlineKeyboardButton(text=button[0], callback_data=button[1]) for button in row])
    if len(selected) > 1:
        new_row = [InlineKeyboardButton(text='Назад', callback_data=selected[-2])]
        if new_row not in keyboard_buttons:
            keyboard_buttons.append(new_row)
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    return keyboard