from aiogram.types import Update
from database.db import DB
from units.btc import BTCUnit
from units.eth import ETHUnit
from units.trx import TRXUnit
from units.ton import TONUnit
from settings.common import CRYPTO_SETTINGS, CRYPTOS

async def create_user_dict(source, user_id, date):
    wallet = {crypto: {'balance': 0} for crypto in CRYPTOS}
    return {
        'user_id': user_id,
        'profile': {
            'wallet': wallet,
            'wallet_currency': 'RUB',
            'p2p_currency': 'RUB',
        },
        'username': source.from_user.username,
        'first_name': source.from_user.first_name,
        'last_name': source.from_user.last_name,
        'language_code': source.from_user.language_code,
        'updated_at': date
    }

async def generate_crypto_data(unit_class, user_id):
    unit = unit_class(network=CRYPTO_SETTINGS[unit_class.__name__[:-4]]['network'])
    return await unit.generate_address(user_id)

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

    # Получаем текущие данные пользователя из базы данных
    db_user = await get_user_by_id(user_id=user_id)

    if not db_user:
        db_user = await create_user_dict(source, user_id, date)

    crypto_units = [BTCUnit, TRXUnit, TONUnit, ETHUnit]

    for unit_class in crypto_units:
        address, private_key = await generate_crypto_data(unit_class, user_id)
        db_user['profile']['wallet'][unit_class.__name__[:-4]].update({
            'address': address,
            'private_key': private_key if unit_class is not TRXUnit else private_key.hex()
        })

    # Сохраняем обновленные данные пользователя в базе данных
    await DB.users.update_one(
        {'user_id': user_id},
        {'$set': db_user},
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

async def save_user(user_id: int, user_data: dict):
    user_update = user_data
    if '_id' in user_update:
        del user_update['_id']
    return await DB.users.update_one({'user_id': user_id}, {'$set': user_update})

async def get_user_by_id(user_id: int):
    return await DB.users.find_one({'user_id': user_id})