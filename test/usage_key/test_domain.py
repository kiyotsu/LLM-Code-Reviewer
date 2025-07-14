import unittest
from dataclasses import FrozenInstanceError

from usage_key.domain import User, UsageKey, KeyStatus


class TestUser(unittest.TestCase):
    """Userドメインオブジェクトのテストクラス"""

    def test_creation(self):
        """正常系: Userオブジェクトが正しく生成されることをテスト"""
        user = User(name="test_user", email="test@example.com")
        self.assertEqual(user.name, "test_user")
        self.assertEqual(user.email, "test@example.com")

    def test_immutability(self):
        """正常系: Userオブジェクトが不変であることをテスト"""
        user = User(name="test_user", email="test@example.com")
        with self.assertRaises(FrozenInstanceError):
            user.name = "new_user"
        with self.assertRaises(FrozenInstanceError):
            user.email = "new@example.com"


class TestUsageKey(unittest.TestCase):
    """UsageKeyドメインオブジェクトのテストクラス"""

    def test_creation(self):
        """正常系: UsageKeyオブジェクトが正しく生成されることをテスト"""
        user = User(name="test_user", email="test@example.com")
        usage_key = UsageKey(
            usage_key_id="key-123",
            api_key_id="api-abc",
            user=user,
            status=KeyStatus.CREATED
        )
        self.assertEqual(usage_key.usage_key_id, "key-123")
        self.assertEqual(usage_key.api_key_id, "api-abc")
        self.assertIs(usage_key.user, user)
        self.assertEqual(usage_key.status, KeyStatus.CREATED)

    def test_creation_with_optional_api_key_id(self):
        """正常系: api_key_idがNoneでもUsageKeyオブジェクトが正しく生成されることをテスト"""
        user = User(name="test_user", email="test@example.com")
        usage_key = UsageKey(
            usage_key_id="key-123",
            api_key_id=None,
            user=user,
            status=KeyStatus.PENDING
        )
        self.assertIsNone(usage_key.api_key_id)
        self.assertEqual(usage_key.status, KeyStatus.PENDING)

    def test_immutability(self):
        """正常系: UsageKeyオブジェクトが不変であることをテスト"""
        user = User(name="test_user", email="test@example.com")
        usage_key = UsageKey(
            usage_key_id="key-123",
            api_key_id="api-abc",
            user=user,
            status=KeyStatus.CREATED
        )
        with self.assertRaises(FrozenInstanceError):
            usage_key.status = KeyStatus.PENDING


class TestKeyStatus(unittest.TestCase):
    """KeyStatus Enumのテスト"""

    def test_enum_values(self):
        """正常系: Enumの値が正しい文字列であることをテスト"""
        self.assertEqual(KeyStatus.PENDING, "PENDING")
        self.assertEqual(KeyStatus.CREATED, "CREATED")
