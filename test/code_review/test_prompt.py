import unittest
from unittest.mock import MagicMock

from code_review.prompt import CodeReviewPrompt, RESPONSE_FORMAT
from code_review.rules import CodingRules


class TestCodeReviewPrompt(unittest.TestCase):
    """CodeReviewPromptのテストクラス"""

    def setUp(self):
        """各テストの前に実行されるセットアップ処理"""
        self.source_code = "def hello():\n    print('world')"
        self.language = "python"
        self.mock_coding_rules = MagicMock(spec=CodingRules)
        self.mock_coding_rules.to_string.return_value = "- Category1: Rule1\n"

        self.prompt = CodeReviewPrompt(
            source_code=self.source_code,
            language=self.language,
            coding_rules=self.mock_coding_rules
        )

    def test_init(self):
        """正常系: __init__で各プロパティが正しく設定されることをテスト"""
        self.assertEqual(self.prompt.source_code, self.source_code)
        self.assertEqual(self.prompt.language, self.language)
        self.assertIs(self.prompt.coding_rules, self.mock_coding_rules)

    def test_create_user_prompt(self):
        """正常系: create_user_promptがソースコードをそのまま返すことをテスト"""
        self.assertEqual(self.prompt.create_user_prompt(), self.source_code)

    def test_create_system_prompt(self):
        """正常系: create_system_promptが正しいシステムプロンプトを生成することをテスト"""
        system_prompt = self.prompt.create_system_prompt()

        self.assertIn(f"You are a professional and experienced **{self.language}**  engineer", system_prompt)
        self.assertIn(self.mock_coding_rules.to_string.return_value, system_prompt)
        self.assertIn(RESPONSE_FORMAT, system_prompt)
        self.mock_coding_rules.to_string.assert_called_once()
