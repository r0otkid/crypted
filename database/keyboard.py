from database.db import DB
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def get_keyboard(keyboard_id):
    keyboard_data = await DB.keyboards.find_one({'keyboard_id': keyboard_id})
    if not keyboard_data:
        return None
    
    keyboard_buttons = []
    for row in keyboard_data['buttons']:
        buttons = [InlineKeyboardButton(text=button[0], callback_data=button[1]) for button in row]
        keyboard_buttons.append(buttons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    return keyboard