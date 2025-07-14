import json
from abc import ABC, abstractmethod
from typing import List


class RuleProviderBase(ABC):
    @abstractmethod
    def load_rules(self) -> dict:
        """
        Example: {"category1": ["rule1-1", "rule1-2"], "category2": ["rule2-1"]}
        """
        pass


class CodingRulesFromFile(RuleProviderBase):
    """ローカルのJSONファイルからコーディングルールを読み込むクラス"""
    def __init__(self, file_path: str):
        self.file_path = file_path

    def load_rules(self) -> dict:
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as error:
            raise ValueError(f"コーディングルールを読み込めませんでした: {self.file_path}") from error


class CodingRules:
    def __init__(self):
        self._rules: List[str] = []

    @property
    def total_count(self) -> int:
        return len(self._rules)

    def add(self, category: str, rule: str):
        if not category or not rule:
            raise ValueError("Coding Rule cannot be empty.")
        self._rules.append({
            "category": category,
            "value": rule
        })

    def to_string(self) -> str:
        rules_string = "".join([f"- {rule['category']}: {rule['value']}\n" for rule in self._rules])
        return rules_string


class CodingRulesBuilder:
    def __init__(self, rule_provider: RuleProviderBase):
        self.coding_rules = CodingRules()
        self._all_rules = rule_provider.load_rules()

    def build(self) -> CodingRules:
        return self.coding_rules

    def enabled_rules(self, category: str) -> "CodingRulesBuilder":
        self._add_rules_by_category(category)
        return self

    def add_all_rules(self) -> "CodingRulesBuilder":
        for category in self._all_rules.keys():
            self._add_rules_by_category(category)
        return self

    def _add_rules_by_category(self, category: str):
        rules_for_category = self._all_rules.get(category, [])
        for rule in rules_for_category:
            self.coding_rules.add(category, rule)
