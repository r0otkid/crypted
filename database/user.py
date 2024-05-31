from aiogram.types import Update
from database.db import DB
from units.btc import BTCUnit
from settings.common import CRYPTO_SETTINGS


async def update_or_create_user(update: Update):
    if update.message:
        source = update.message
        date = source.date
    elif update.callback_query:
        source = update.callback_query
        date = source.message.date
    else:
        return
    user_id = source.from_user.id
    btc_unit = BTCUnit(network=CRYPTO_SETTINGS['BTC']['network'])
    btc_address, private_key = await btc_unit.generate_address(user_id)
    profile_data = {
        "wallet_currency": "RUB",
        "p2p_currency": "RUB",
        "address": {
            "BTC": btc_address,
            "private_key": private_key
        }
    }
    user_data = {
        'user_id': user_id,
        'profile': profile_data,
        'username': source.from_user.username,
        'first_name': source.from_user.first_name,
        'last_name': source.from_user.last_name,
        'language_code': source.from_user.language_code,
        'updated_at': date
    }
    
    await DB.users.update_one(
        {'user_id': user_id},
        {'$set': user_data},
        upsert=True
    )

async def get_user(update: Update):
    if update.message:
        user_id = update.message.from_user.id
    elif update.callback_query:
        user_id = update.callback_query.from_user.id
    elif update.inline_query:
        user_id = update.inline_query.from_user.id
    elif update.chosen_inline_result:
        user_id = update.chosen_inline_result.from_user.id
    else:
        return None

    user = await DB.users.find_one({'user_id': user_id})
    return user