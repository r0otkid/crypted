import time
from typing import Optional
import uuid
import base64
from settings.common import CRYPTO_SETTINGS, BTC, TRX, TON, ETH
from units.base import Unit
from units.btc import BTCUnit
from units.eth import ETHUnit
from units.trx import TRXUnit
from units.ton import TONUnit

ALL_UNITS = [BTCUnit, ETHUnit, TRXUnit, TONUnit]

def generate_unique_code():
    # Создаем UUID4
    uuid_bytes = uuid.uuid4().bytes
    # Кодируем в base64 и удаляем ненужные символы
    code = base64.urlsafe_b64encode(uuid_bytes).rstrip(b'=').decode('ascii')
    return code[:12]


def get_unit(crypto: str) -> Optional[Unit]:
    if not crypto in CRYPTO_SETTINGS:
        raise ValueError(f'Unknown cryptocurrency: {crypto}')
    return {
        BTC: BTCUnit,
        ETH: ETHUnit,
        TRX: TRXUnit,
        TON: TONUnit,
    }[crypto]
