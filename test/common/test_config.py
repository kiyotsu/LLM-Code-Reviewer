import unittest
from unittest.mock import MagicMock

from botocore.exceptions import ClientError

from common.config import SsmConfigLoader
from common.exception import Boto3Exception


class TestSsmConfigLoader(unittest.TestCase):

    def setUp(self):
        """各テストの前に実行されるセットアップ処理"""
        # boto3クライアントのモックを作成
        self.mock_ssm_client = MagicMock()
        self.parameter_path_prefix = "/llm-code-reviewer/dev/"

        # SsmConfigLoaderのクラスレベルのキャッシュを各テストの前にクリア
        SsmConfigLoader._cache.clear()

        # テスト対象のクラスをインスタンス化
        self.loader = SsmConfigLoader(self.mock_ssm_client, self.parameter_path_prefix)

    def test_load_config_success_and_nesting(self):
        """SSMからパラメータを正常に取得し、ネストした辞書を構築できることをテスト"""
        path_suffix = "codereview"
        full_path = f"{self.parameter_path_prefix}{path_suffix}/"

        # SSMから返されるであろうパラメータのモックデータ
        mock_ssm_response_page = {
            'Parameters': [
                {'Name': f'{full_path}bedrock/ModelId', 'Value': 'anthropic.claude-3-sonnet'},
                {'Name': f'{full_path}bedrock/MaxTokens', 'Value': '2048'},
                {'Name': f'{full_path}bedrock/Temperature', 'Value': '0.7'},
                {'Name': f'{full_path}other/SomeValue', 'Value': 'test'},
            ]
        }

        # paginatorがモックデータを返すように設定
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [mock_ssm_response_page]
        self.mock_ssm_client.get_paginator.return_value = mock_paginator

        # メソッドを実行
        result_config = self.loader.load_config(path_suffix)

        # 期待される結果
        expected_config = {
            "bedrock": {
                "ModelId": "anthropic.claude-3-sonnet",
                "MaxTokens": "2048",
                "Temperature": "0.7"
            },
            "other": {
                "SomeValue": "test"
            }
        }
        print(result_config)
        # 結果が期待通りであることをアサート
        self.assertEqual(result_config, expected_config)

        # get_paginatorとpaginateが正しく呼び出されたことを確認
        self.mock_ssm_client.get_paginator.assert_called_once_with('get_parameters_by_path')
        mock_paginator.paginate.assert_called_once_with(
            Path=full_path,
            Recursive=True,
            WithDecryption=True
        )

    def test_load_config_uses_cache(self):
        """2回目の呼び出しでキャッシュが使用され、SSMへのAPIコールが発生しないことをテスト"""
        path_suffix = "codereview"

        # 1回目の呼び出しでSSMをモック
        mock_paginator = MagicMock()
        mock_paginator.paginate.return_value = [{'Parameters': []}]
        self.mock_ssm_client.get_paginator.return_value = mock_paginator

        # 1回目の呼び出し（キャッシュに格納される）
        self.loader.load_config(path_suffix)
        self.mock_ssm_client.get_paginator.assert_called_once()

        # モックの呼び出し回数をリセット
        self.mock_ssm_client.get_paginator.reset_mock()

        # 2回目の呼び出し
        self.loader.load_config(path_suffix)

        # SSMへのAPIコールが発生していないことを確認
        self.mock_ssm_client.get_paginator.assert_not_called()

    def test_load_config_handles_client_error(self):
        """boto3のClientErrorが発生した際にBoto3Exceptionを送出することをテスト"""
        path_suffix = "codereview"
        error_response = {'Error': {'Code': 'AccessDeniedException', 'Message': 'Access Denied'}}

        # paginatorがClientErrorを発生させるように設定
        self.mock_ssm_client.get_paginator.side_effect = ClientError(error_response, 'get_parameters_by_path')

        # Boto3Exceptionが送出されることをコンテキストマネージャで確認
        with self.assertRaises(Boto3Exception) as cm:
            self.loader.load_config(path_suffix)

        # 例外オブジェクトのプロパティが正しいことを確認
        self.assertEqual(cm.exception.service, "ssm")
        self.assertEqual(cm.exception.reason, "AccessDeniedException")
