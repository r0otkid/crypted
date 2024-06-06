from database.db import DB

async def get_all_rates():
    return await DB.rates.find_one({})

async def update_or_create_rates(rates: dict):
    await DB.rates.update_one({}, {'$set': rates}, upsert=True)