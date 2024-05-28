import logging
from aiohttp import web
from aiogram import Bot, types
from dispatcher import CustomDispatcher, handle_callback_query, handle_message
from settings.common import BOT_TOKEN, BASE_URL

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
        await dispatcher.handle_webhook(self.request, bot=bot)
        return web.Response(status=200)

async def set_webhook(app):
    await bot.delete_webhook()
    webhook_url = f'{BASE_URL}/{BOT_TOKEN}/'
    await bot.set_webhook(webhook_url)
    logging.info(f'Webhook set to {webhook_url}')

app = web.Application()
app.router.add_view('/{bot_token}/', WebHookView)
app.on_startup.append(set_webhook)

if __name__ == '__main__':
    web.run_app(app, host='127.0.0.1', port=7878)