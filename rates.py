import logging
import aiohttp
import asyncio
from database.db import DB
from typing import Dict
from settings.common import CRYPTO_COMPARE_API_KEY, CRYPTOS

class CryptoRatesUpdater:
    def __init__(self, update_interval: int = 60, api_key: str = CRYPTO_COMPARE_API_KEY):
        self.update_interval = update_interval
        self.api_key = api_key
        self.api_url = 'https://min-api.cryptocompare.com/data/price'
        self.cryptos = CRYPTOS

    async def fetch_rate(self, session: aiohttp.ClientSession, crypto: str) -> float:
        params = {
            'fsym': crypto,
            'tsyms': 'USD',
            'api_key': self.api_key
        }
        async with session.get(self.api_url, params=params) as response:
            data = await response.json()
            return data['USD']

    async def fetch_all_rates(self) -> Dict[str, float]:
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_rate(session, crypto) for crypto in self.cryptos]
            rates = await asyncio.gather(*tasks)
            return dict(zip(self.cryptos, rates))

    async def update_rates(self):
        while True:
            logging.info('Updating rates...')
            rates = await self.fetch_all_rates()
            rates = {**rates, 'RUB': 69.1}  # todo: hardcoded rub rates
            logging.info(rates)
            await self.update_or_create_rates(rates)
            await asyncio.sleep(self.update_interval)

    async def update_or_create_rates(self, rates: Dict[str, float]):
        await DB.rates.update_one({}, {'$set': rates}, upsert=True)

    async def start(self, app):
        await self.update_rates()