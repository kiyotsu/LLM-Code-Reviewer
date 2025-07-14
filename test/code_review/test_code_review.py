import os
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from botocore.exceptions import ClientError

from code_review.code_review import (
    CodeReviewModelConfig, CodeReviewService, CodeReviewServiceContext
)
from code_review.rules import RuleProviderBase
from common.exception import Boto3Exception


class TestCodeReviewModelConfig(unittest.TestCase):
    """CodeReviewModelConfigのテストクラス"""

    def test_init_success(self):
        """正常系: 正しい型の文字列が渡された場合に、正しくインスタンスが生成されることをテスト"""
        config = CodeReviewModelConfig(
            model_id="model-1",
            token_max="2048",
            temperature="0.7",
            top_p="0.9"
        )
        self.assertEqual(config.model_id, "model-1")
        self.assertEqual(config.token_max, 2048)
        self.assertEqual(config.temperature, 0.7)
        self.assertEqual(config.top_p, 0.9)

    def test_init_invalid_token_max(self):
        """異常系: token_maxに整数変換できない文字列が渡された場合にValueErrorが発生することをテスト"""
        with self.assertRaisesRegex(ValueError, "'token_max' must be an integer"):
            CodeReviewModelConfig("m", "invalid", "0.7", "0.9")

    def test_init_invalid_temperature(self):
        """異常系: temperatureにfloat変換できない文字列が渡された場合にValueErrorが発生することをテスト"""
        with self.assertRaisesRegex(ValueError, "'temperature' must be an float"):
            CodeReviewModelConfig("m", "2048", "invalid", "0.9")

    def test_init_invalid_top_p(self):
        """異常系: top_pにfloat変換できない文字列が渡された場合にValueErrorが発生することをテスト"""
        with self.assertRaisesRegex(ValueError, "'top_p' must be an float"):
            CodeReviewModelConfig("m", "2048", "0.7", "invalid")


class TestCodeReviewService(unittest.TestCase):
    """CodeReviewServiceのテストクラス"""

    def setUp(self):
        """各テストの前に実行されるセットアップ処理"""
        self.mock_bedrock_client = MagicMock()
        self.mock_model_config = CodeReviewModelConfig(
            model_id="test-model",
            token_max="1024",
            temperature="0.5",
            top_p="1.0"
        )
        self.mock_rule_provider = MagicMock(spec=RuleProviderBase)
        self.mock_rule_provider.load_rules.return_value = {
            "TestCategory": ["Test Rule 1"]
        }

        self.service = CodeReviewService(
            bedrock=self.mock_bedrock_client,
            model_config=self.mock_model_config,
            rule_provider=self.mock_rule_provider
        )

    @patch('code_review.code_review.CodeReviewPrompt')
    @patch('code_review.code_review.CodingRulesBuilder')
    def test_excute_review_success(self, MockCodingRulesBuilder, MockCodeReviewPrompt):
        """正常系: コードレビューが正常に実行され、結果が返されることをテスト"""
        # --- モックの設定 ---
        mock_builder_instance = MockCodingRulesBuilder.return_value
        mock_builder_instance.add_all_rules.return_value = mock_builder_instance
        mock_builder_instance.build.return_value.to_string.return_value = "- TestCategory: Test Rule 1\n"
        mock_builder_instance.build.return_value.total_count = 1

        mock_prompt_instance = MockCodeReviewPrompt.return_value
        mock_prompt_instance.create_system_prompt.return_value = "system prompt"
        mock_prompt_instance.create_user_prompt.return_value = "user prompt"

        mock_response = {
            "output": {"message": {"content": [{"text": '{"review_result": "OK"}'}]}},
            "usage": {"input_tokens": 10, "output_tokens": 5}
        }
        self.mock_bedrock_client.converse.return_value = mock_response

        # --- メソッドの実行 ---
        source_code = "print('hello')"
        language = "python"
        result = self.service.excute_review(source_code, language)

        # --- アサーション ---
        MockCodingRulesBuilder.assert_called_once_with(self.mock_rule_provider)
        mock_builder_instance.add_all_rules.assert_called_once()

        MockCodeReviewPrompt.assert_called_once()
        prompt_args, prompt_kwargs = MockCodeReviewPrompt.call_args
        self.assertEqual(prompt_kwargs['source_code'], source_code)
        self.assertEqual(prompt_kwargs['language'], language)

        self.mock_bedrock_client.converse.assert_called_once()
        converse_args, converse_kwargs = self.mock_bedrock_client.converse.call_args
        self.assertEqual(converse_kwargs['modelId'], self.mock_model_config.model_id)
        self.assertEqual(converse_kwargs['messages'][0]['content'][0]['text'], "user prompt")
        self.assertEqual(converse_kwargs['system'][0]['text'], "system prompt")
        self.assertEqual(converse_kwargs['inferenceConfig']['maxTokens'], self.mock_model_config.token_max)

        self.assertEqual(result, {"review_result": "OK"})

    def test_excute_review_boto3_error(self):
        """異常系: Bedrock API呼び出しでClientErrorが発生した場合にBoto3Exceptionを送出することをテスト"""
        error_response = {'Error': {'Code': 'ThrottlingException', 'Message': 'Rate exceeded'}}
        self.mock_bedrock_client.converse.side_effect = ClientError(error_response, 'Converse')

        with self.assertRaises(Boto3Exception):
            self.service.excute_review("print('hello')", "python")


@patch.dict(os.environ, {"PARAMETER_PATH_PREFIX": "/test/prefix/"})
class TestCodeReviewServiceContext(unittest.TestCase):
    """CodeReviewServiceContextのテストクラス"""

    def setUp(self):
        """各テストの前にlru_cacheをクリアし、テスト間の依存をなくす"""
        # NOTE: 各プロパティはlru_cacheでデコレートされているため、fget経由でキャッシュをクリアする
        CodeReviewServiceContext.ssm_config_loader.fget.cache_clear()
        CodeReviewServiceContext.bedrock_config.fget.cache_clear()
        CodeReviewServiceContext.ssm_client.fget.cache_clear()
        CodeReviewServiceContext.bedrock_client.fget.cache_clear()
        CodeReviewServiceContext.rule_provider.fget.cache_clear()
        CodeReviewServiceContext.model_config.fget.cache_clear()
        CodeReviewServiceContext.code_review_service.fget.cache_clear()

        self.context = CodeReviewServiceContext()

    @patch("code_review.code_review.boto3.client")
    def test_clients_cached(self, mock_boto3_client):
        """ssm_clientとbedrock_clientがキャッシュされることをテスト"""
        # ssm_clientのテスト
        ssm_client1 = self.context.ssm_client
        ssm_client2 = self.context.ssm_client
        self.assertIs(ssm_client1, ssm_client2)
        mock_boto3_client.assert_called_with("ssm")

        # bedrock_clientのテスト
        bedrock_client1 = self.context.bedrock_client
        bedrock_client2 = self.context.bedrock_client
        self.assertIs(bedrock_client1, bedrock_client2)
        mock_boto3_client.assert_called_with("bedrock-runtime")

        # boto3.clientの呼び出し回数がそれぞれ1回であることを確認
        self.assertEqual(mock_boto3_client.call_count, 2)

    @patch("code_review.code_review.SsmConfigLoader")
    def test_ssm_config_loader_cached(self, MockSsmConfigLoader):
        """ssm_config_loaderがキャッシュされることをテスト"""
        with patch.object(CodeReviewServiceContext, 'ssm_client', new_callable=PropertyMock) as mock_ssm_client_prop:
            mock_ssm_client_prop.return_value = MagicMock()

            loader1 = self.context.ssm_config_loader
            loader2 = self.context.ssm_config_loader

            self.assertIs(loader1, loader2)
            MockSsmConfigLoader.assert_called_once_with(
                mock_ssm_client_prop.return_value,
                "/test/prefix/"
            )

    @patch("code_review.code_review.CodingRulesFromFile")
    def test_rule_provider_cached(self, MockCodingRulesFromFile):
        """rule_providerがキャッシュされることをテスト"""
        provider1 = self.context.rule_provider
        provider2 = self.context.rule_provider
        self.assertIs(provider1, provider2)
        MockCodingRulesFromFile.assert_called_once()
        # Check that the path is correct
        args, _ = MockCodingRulesFromFile.call_args
        self.assertTrue(args[0].endswith("rules.json"))

    @patch("code_review.code_review.CodeReviewModelConfig")
    def test_model_config_cached(self, MockCodeReviewModelConfig):
        """model_configがキャッシュされることをテスト"""
        mock_config_dict = {
            "ModelId": "model-id-from-ssm",
            "MaxTokens": "4096",
            "Temperature": "0.1",
            "TopP": "0.8"
        }
        with patch.object(CodeReviewServiceContext, 'bedrock_config', new_callable=PropertyMock) as mock_bedrock_config_prop:
            mock_bedrock_config_prop.return_value = mock_config_dict

            config1 = self.context.model_config
            config2 = self.context.model_config

            self.assertIs(config1, config2)
            MockCodeReviewModelConfig.assert_called_once_with(
                "model-id-from-ssm", "4096", "0.1", "0.8"
            )

    @patch("code_review.code_review.CodeReviewService")
    def test_code_review_service_cached(self, MockCodeReviewService):
        """code_review_serviceがキャッシュされることをテスト"""
        with patch.object(CodeReviewServiceContext, 'bedrock_client', new_callable=PropertyMock) as mock_bedrock_client, \
             patch.object(CodeReviewServiceContext, 'model_config', new_callable=PropertyMock) as mock_model_config, \
             patch.object(CodeReviewServiceContext, 'rule_provider', new_callable=PropertyMock) as mock_rule_provider:

            mock_bedrock_client.return_value = MagicMock()
            mock_model_config.return_value = MagicMock()
            mock_rule_provider.return_value = MagicMock()

            service1 = self.context.code_review_service
            service2 = self.context.code_review_service

            self.assertIs(service1, service2)
            MockCodeReviewService.assert_called_once_with(
                mock_bedrock_client.return_value,
                mock_model_config.return_value,
                mock_rule_provider.return_value
            )

    def test_bedrock_config_cached(self):
        """bedrock_configがキャッシュされ、SsmConfigLoaderの呼び出しが一度だけ行われることをテスト"""
        # --- モックの設定 ---
        # ssm_config_loaderプロパティが返すモックインスタンスを作成
        mock_loader_instance = MagicMock()
        # load_configメソッドが返す値を設定
        mock_config_data = {"ModelId": "test-model-from-ssm"}
        mock_loader_instance.load_config.return_value = mock_config_data

        # CodeReviewServiceContext.ssm_config_loaderが、上記で設定したモックインスタンスを返すようにパッチを当てる
        with patch.object(CodeReviewServiceContext, 'ssm_config_loader', new_callable=PropertyMock) as mock_ssm_loader_prop:
            mock_ssm_loader_prop.return_value = mock_loader_instance

            # --- メソッドの実行 ---
            config1 = self.context.bedrock_config
            config2 = self.context.bedrock_config

            # --- アサーション ---
            self.assertIs(config1, config2)  # キャッシュにより同じオブジェクトが返される
            self.assertEqual(config1, mock_config_data)  # 内容が正しい
            # SsmConfigLoader.load_configが "bedrock" を引数に1回だけ呼び出されたことを確認
            mock_loader_instance.load_config.assert_called_once_with("bedrock")
