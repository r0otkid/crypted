from context.base import DefaultContext
from gettext import gettext as _

class SettingsContext(DefaultContext):
    async def ctx(self):
        return {
            'user': self.user['first_name'],
            'market_currency': 'RUB',
            'wallet_currency': 'RUB',
            'comment': _('без комментария'),
            'energy': 0.5
        }