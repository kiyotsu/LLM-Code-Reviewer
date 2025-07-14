import unittest
import json
from unittest.mock import patch, mock_open, MagicMock

from code_review.rules import (
    CodingRulesFromFile,
    CodingRules,
    CodingRulesBuilder,
    RuleProviderBase,
)


class TestCodingRules(unittest.TestCase):
    def test_add_and_to_string(self):
        rules = CodingRules()
        rules.add("Readability", "Use clear variable names.")
        rules.add("Performance", "Avoid nested loops.")

        self.assertEqual(rules.total_count, 2)
        expected_string = "- Readability: Use clear variable names.\n- Performance: Avoid nested loops.\n"
        self.assertEqual(rules.to_string(), expected_string)

    def test_add_empty_rule_raises_value_error(self):
        rules = CodingRules()
        with self.assertRaisesRegex(ValueError, "Coding Rule cannot be empty."):
            rules.add("", "Some rule")
        with self.assertRaisesRegex(ValueError, "Coding Rule cannot be empty."):
            rules.add("Category", "")


class TestCodingRulesFromFile(unittest.TestCase):
    def test_load_rules_success(self):
        mock_file_content = json.dumps({
            "Readability": ["Rule 1"],
            "Maintainability": ["Rule 2"]
        })
        # mock_openでファイル読み込みをモック
        with patch("builtins.open", mock_open(read_data=mock_file_content)) as mock_file:
            provider = CodingRulesFromFile("dummy/path/rules.json")
            rules = provider.load_rules()

            mock_file.assert_called_once_with("dummy/path/rules.json", "r", encoding="utf-8")
            self.assertEqual(rules, {"Readability": ["Rule 1"], "Maintainability": ["Rule 2"]})

    def test_load_rules_file_not_found(self):
        with patch("builtins.open", side_effect=FileNotFoundError):
            provider = CodingRulesFromFile("nonexistent/path/rules.json")
            with self.assertRaisesRegex(ValueError, "コーディングルールを読み込めませんでした"):
                provider.load_rules()

    def test_load_rules_invalid_json(self):
        mock_file_content = "this is not json"
        with patch("builtins.open", mock_open(read_data=mock_file_content)):
            provider = CodingRulesFromFile("dummy/path/rules.json")
            with self.assertRaisesRegex(ValueError, "コーディングルールを読み込めませんでした"):
                provider.load_rules()


class TestCodingRulesBuilder(unittest.TestCase):
    def setUp(self):
        # モックのRuleProviderを作成
        self.mock_rule_provider = MagicMock(spec=RuleProviderBase)
        self.mock_rules_data = {
            "Readability": ["Readable Rule 1", "Readable Rule 2"],
            "Performance": ["Performance Rule 1"]
        }
        self.mock_rule_provider.load_rules.return_value = self.mock_rules_data

    def test_build_empty(self):
        builder = CodingRulesBuilder(self.mock_rule_provider)
        # 何も追加せずにビルド
        rules = builder.build()
        self.assertEqual(rules.total_count, 0)

    def test_add_all_rules(self):
        builder = CodingRulesBuilder(self.mock_rule_provider)
        rules = builder.add_all_rules().build()

        self.assertEqual(rules.total_count, 3)
        # ルールの順序は保証されないため、setで比較
        expected_rules_set = {
            "- Readability: Readable Rule 1",
            "- Readability: Readable Rule 2",
            "- Performance: Performance Rule 1",
        }
        self.assertEqual(set(rules.to_string().strip().split('\n')), expected_rules_set)

    def test_enabled_rules(self):
        builder = CodingRulesBuilder(self.mock_rule_provider)
        rules = builder.enabled_rules("Readability").build()

        self.assertEqual(rules.total_count, 2)
        expected_string = "- Readability: Readable Rule 1\n- Readability: Readable Rule 2\n"
        self.assertEqual(rules.to_string(), expected_string)
