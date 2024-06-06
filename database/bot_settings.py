from database.db import DB
from settings.common import BOT_NAME
from triggers import Triggers

async def get_or_create_bot_settings() -> dict:
    bot_settings = await DB.bot_settings.find_one({})
    if not bot_settings:
        bot_settings = {
            "limits": {
                Triggers.BTC: {
                    "min": 0.0001,
                    "max": 0.1
                },
                Triggers.ETH: {
                    "min": 0.001,
                    "max": 1
                },
                Triggers.TRX: {
                    "min": 1,
                    "max": 10000
                },
                Triggers.TON: {
                    "min": 1,
                    "max": 1000
                }
            },
            "pagination": {
                "per_page": 5
            },
            "links": {
                "channel": "https://t.me/",
                "chat": "https://t.me/",
            }
        }
        await DB.bot_settings.insert_one(bot_settings)
    return bot_settings