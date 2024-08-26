import asyncio
import logging
from traceback import print_tb
from aiohttp import web
from aiogram import Bot, types
from database.db import DB
from dispatcher import CustomDispatcher, handle_callback_query, handle_message
from rates import CryptoRatesUpdater
from settings.common import BOT_TOKEN, BASE_URL, CRYPTO_SETTINGS
from utils import ALL_UNITS

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)

dispatcher = CustomDispatcher()
dispatcher.register_handler(types.message.Message, handle_message)
dispatcher.register_handler(types.callback_query.CallbackQuery, handle_callback_query)

class WebHookView(web.View):
    async def post(self):
        bot_token = self.request.match_info.get('bot_token')
        if bot_token != BOT_TOKEN:
            return web.Response(status=403)
        try:
            await dispatcher.handle_webhook(self.request, bot=bot)
        except Exception as global_error:
            logging.error(global_error)
            print_tb(global_error.__traceback__)
            logging.error('Error while processing webhook')
        return web.Response(status=200)

async def set_webhook(app):
    await bot.delete_webhook()
    webhook_url = f'{BASE_URL}/{BOT_TOKEN}/'
    await bot.set_webhook(webhook_url)
    logging.info(f'Webhook set to {webhook_url}')
    
async def get_network_fees(app):
    def _get_crypto(unit):
        return unit.__name__[:-4]
    for unit in ALL_UNITS:
        if _get_crypto(unit) in CRYPTO_SETTINGS:
            network = CRYPTO_SETTINGS[_get_crypto(unit)]['network']
            network_fee = await unit(network=network).get_network_fee()
            await DB.network_fees.update_one({'crypto': _get_crypto(unit)}, {'$set': {'network_fee': str(network_fee)}}, upsert=True)

app = web.Application()
updater = CryptoRatesUpdater(update_interval=60)

app.router.add_view('/{bot_token}/', WebHookView)
app.on_startup.append(set_webhook)
app.on_startup.append(get_network_fees)
# app.on_startup.append(updater.start)


if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=7878)