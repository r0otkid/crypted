from base64 import b64encode
import unittest
from unittest.mock import patch, AsyncMock
from tests.base import BaseCryptedTestCase
from units.ton import TONUnit


class TestTONUnit(BaseCryptedTestCase):

    def setUp(self):
        self.ton_unit = TONUnit(network='testnet', access_key='fake_access_key')

    def test_initialization_mainnet(self):
        ton_unit_mainnet = TONUnit(network='mainnet', access_key='fake_access_key')
        self.assertEqual(ton_unit_mainnet.base_url, "https://toncenter.com")
        self.assertEqual(ton_unit_mainnet.network, 'mainnet')

    def test_initialization_testnet(self):
        self.assertEqual(self.ton_unit.base_url, "https://testnet.toncenter.com")
        self.assertEqual(self.ton_unit.network, 'testnet')

    def test_invalid_network(self):
        with self.assertRaises(ValueError):
            TONUnit(network='invalid_network')

    def test_get_wallet_url(self):
        address = "fake_address"
        self.assertEqual(self.ton_unit.get_wallet_url(address), f'https://testnet.tonscan.org/address/{address}')

    @patch('nacl.signing.SigningKey')
    def test_generate_address(self, mock_signing_key):
        # Создаем поддельный ключ с четным количеством символов
        mock_key_pair = {
            'public': 'a'*64,  # 64 символа - допустимая длина для публичного ключа в hex формате
            'secret': 'b'*64  # 64 символа для приватного ключа
        }
        
        # Настройка mock
        mock_signing_key.return_value.verify_key.encode.return_value = mock_key_pair['public'].encode('utf-8')
        mock_signing_key.return_value.encode.return_value = mock_key_pair['secret'].encode('utf-8')
        
        # Генерация адреса
        generated_address = self.ton_unit.generate_address(user_id=123)
        
        # Assertions или вывод
        print(generated_address)

    def test_mnemonic_from_entropy(self):
        entropy = b'\x00' * 32
        mnemonic = self.ton_unit._mnemonic_from_entropy(entropy)
        self.assertIsInstance(mnemonic, str)

    @patch('hashlib.sha256')
    @patch('nacl.signing.SigningKey')
    def test_derive_sign_keys(self, mock_signing_key, mock_sha256):
        mock_sha256.return_value.digest.return_value = b'\x00' * 32
        mock_signing_key.return_value.verify_key.encode.return_value = b'fake_public_key'
        mock_signing_key.return_value.encode.return_value = b'fake_secret_key'

        keys = self.ton_unit._derive_sign_keys('fake_phrase')
        self.assertEqual(keys['public'], 'fake_public_key')
        self.assertEqual(keys['secret'], 'fake_secret_key')

    @patch('aiohttp.ClientSession.get')
    @patch('database.db.DB.users.find_one', new_callable=AsyncMock)
    async def test_get_balance(self, mock_find_one, mock_get):
        mock_find_one.return_value = {'user_id': 123}
        mock_response = AsyncMock()
        mock_response.json.return_value = {'ok': True, 'result': 1000000000}
        mock_get.return_value.__aenter__.return_value = mock_response

        balance = await self.ton_unit.get_balance('fake_address')
        self.assertEqual(balance, 0.0)

    def test_estimate_transaction_size(self):
        size = self.ton_unit.estimate_transaction_size()
        self.assertEqual(size, 0.5)

    def test_from_satoshis(self):
        fee_in_nano = 1000000000  # 1 TON
        fee_in_ton = self.ton_unit.from_satoshis(fee_in_nano)
        self.assertEqual(fee_in_ton, 1.0)

    async def test_work_flow(self):
        public, secret = await self.ton_unit.generate_address(user_id=111)
        self.assertIsNotNone(public)
        self.assertIsNotNone(secret)

if __name__ == '__main__':
    unittest.main()
