class BaseTriggers:
    START = '/start'
    BTC = 'BTC'
    TON = 'TON'
    USER_INPUT = 'user_input'

class CheckTriggers:
    CHECK = 'check'
    CREATE_CHECK = 'create_check'
    CHECK_AMOUNT = 'check_amount'

class BillTriggers:
    BILL = 'bill'
    CREATE_BILL = 'create_bill'
    BILL_AMOUNT = 'bill_amount'


class WalletTriggers(CheckTriggers, BillTriggers):
    WALLET = 'wallet'
    REPLENISH = 'replenish'
    WITHDRAW = 'withdraw'

class Triggers(BaseTriggers, WalletTriggers):
    WALLET = 'wallet'
    SETTINGS = 'settings'
    P2P = 'p2p'
    STOCK = 'stock'

def get_all_triggers(cls):
    triggers = []
    for base_class in cls.__mro__:
        if base_class == object:
            continue
        for key, value in vars(base_class).items():
            if not key.startswith('__') and not callable(value):
                triggers.append(value)
    return triggers