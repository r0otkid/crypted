from database.db import DB

class States:
    SELECTED = 'selected_values'
    LAST_MESSAGE = 'last_message'

async def get_state(user_id, key=None) -> dict:
    state = await DB.states.find_one({'user_id': user_id}) or {}
    return state.get(key, {}) if key else state

async def set_state(user_id, key, value):
    state = await get_state(user_id=user_id)
    state[key] = value
    await DB.states.update_one(
        {'user_id': user_id},
        {'$set': state},
        upsert=True
    )
