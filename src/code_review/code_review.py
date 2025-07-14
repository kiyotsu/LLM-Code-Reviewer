import os
import json
import logging
from functools import lru_cache
from typing import Dict

import boto3
from botocore.exceptions import ClientError

from code_review.rules import RuleProviderBase, CodingRulesBuilder, CodingRulesFromFile
from code_review.prompt import CodeReviewPrompt
from common.config import SsmConfigLoader
from common.exception import Boto3Exception


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class CodeReviewModelConfig:
    def __init__(
        self,
        model_id: str,
        token_max: int,
        temperature: float,
        top_p: float,
    ):
        self.model_id = model_id

        try:
            self.token_max = int(token_max)
        except Exception:
            raise ValueError("'token_max' must be an integer")

        try:
            self.temperature = float(temperature)
        except Exception:
            raise ValueError("'temperature' must be an float")

        try:
            self.top_p = float(top_p)
        except Exception:
            raise ValueError("'top_p' must be an float")


class CodeReviewService:
    def __init__(
        self,
        bedrock: "BedrockRuntime",
        model_config: CodeReviewModelConfig,
        rule_provider: RuleProviderBase
    ):
        self.bedrock = bedrock
        self.model_config = model_config
        self.rule_provider = rule_provider

    def excute_review(self, source_code: str, language: str) -> Dict:
        """
        コードレビューを実行する
        Args:
            source_code: ソースコード文字列
            language: プログラミング言語種別を表した文字列
        Returns:
            コードレビュー結果(JSON形式)
            フォーマットはprompt.RESPONSE_FORMATを参照してください。
        """

        # --- コーディングルール定義オブジェクト生成 ---
        coding_rules = CodingRulesBuilder(self.rule_provider).add_all_rules().build()

        # --- コードレビュー用のプロンプトを作成 ---
        prompt = CodeReviewPrompt(
            source_code=source_code,
            language=language,
            coding_rules=coding_rules,
        )
        system_prompt_text = prompt.create_system_prompt()
        user_prompt_text = prompt.create_user_prompt()

        logger.info("プロンプトを開始します....")
        logger.info(f"モデル:{self.model_config.model_id}")
        logger.info(f"コーディングルール数:{coding_rules.total_count}")
        logger.info(f"プロンプト文字列長:{len(system_prompt_text) + len(user_prompt_text)}")

        # --- Bedrockにメッセージ(プロンプト)を送信 ---
        try:
            response = self.bedrock.converse(
                modelId=self.model_config.model_id,
                messages=[{
                    "role": "user",
                    "content": [{"text": user_prompt_text}],
                }],
                system=[{
                    "text": system_prompt_text,
                }],
                inferenceConfig={
                    "maxTokens": self.model_config.token_max,
                    "temperature": self.model_config.temperature,
                    "topP": self.model_config.top_p,
                },
            )

        except ClientError as error:
            raise Boto3Exception(service="bedrock") from error

        # --- レスポンスデータ(フィードバック)を取得 ---
        response_text = response["output"]["message"]["content"][0]["text"]
        logger.info(f'bedrock response:{response_text}')
        logger.info(f'bedrock usage:{response["usage"]}')

        review_result = json.loads(response_text)
        return review_result


class CodeReviewServiceContext:
    @property
    @lru_cache(maxsize=None)
    def ssm_config_loader(self) -> SsmConfigLoader:
        parameter_path_prefix = os.environ.get("PARAMETER_PATH_PREFIX")
        return SsmConfigLoader(self.ssm_client, parameter_path_prefix)

    @property
    @lru_cache(maxsize=None)
    def bedrock_config(self) -> dict:
        return self.ssm_config_loader.load_config("bedrock")

    @property
    @lru_cache(maxsize=None)
    def ssm_client(self):
        return boto3.client("ssm")

    @property
    @lru_cache(maxsize=None)
    def bedrock_client(self):
        return boto3.client("bedrock-runtime")

    @property
    @lru_cache(maxsize=None)
    def rule_provider(self) -> RuleProviderBase:
        rules_file_path = os.path.join(os.path.dirname(__file__), "rules.json")
        return CodingRulesFromFile(rules_file_path)

    @property
    @lru_cache(maxsize=None)
    def model_config(self) -> CodeReviewModelConfig:
        bedrock_config = self.bedrock_config
        return CodeReviewModelConfig(
            bedrock_config["ModelId"],
            bedrock_config["MaxTokens"],
            bedrock_config["Temperature"],
            bedrock_config["TopP"]
        )

    @property
    @lru_cache(maxsize=None)
    def code_review_service(self) -> CodeReviewService:
        """メインのコードレビューサービスインスタンスを提供します。"""
        return CodeReviewService(
            self.bedrock_client,
            self.model_config,
            self.rule_provider
        )
