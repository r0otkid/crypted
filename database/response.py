from database.db import DB

async def get_response(trigger):
    return await DB.responses.find_one({'trigger': trigger})