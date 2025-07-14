import json
import os
import unittest
from unittest.mock import MagicMock, patch

# テスト対象のハンドラをトップレベルでインポート
from usage_key.main import (
    create_usage_key_handler, issutance_request_handler
)


# テスト実行時に環境変数を設定
@patch.dict(os.environ, {"PARAMETER_PATH_PREFIX": "/test/prefix/"})
class TestIssutanceRequestHandler(unittest.TestCase):
    """issutance_request_handlerのテストクラス"""

    def _create_event(self, body, is_json_string=True):
        """テスト用のAPI Gatewayイベントを作成するヘルパーメソッド"""
        if is_json_string:
            return {"body": json.dumps(body)}
        return {"body": body}

    def _create_context(self):
        """テスト用のLambdaコンテキストを作成するヘルパーメソッド"""
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        return context

    # ハンドラが依存するオブジェクトをパッチで差し替える
    @patch("usage_key.main.logger")
    @patch("usage_key.main.ApiResponseBuilder")
    @patch("usage_key.main.User")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_success_with_json_body(
        self, mock_context, mock_user, mock_builder, mock_logger
    ):
        """正常系: bodyがJSON文字列の場合に正しく処理されること"""
        # --- 準備 ---
        mock_service = mock_context.usage_key_service
        mock_usage_key = MagicMock()
        mock_usage_key.status = "REQUESTED"
        mock_service.request_issuance.return_value = mock_usage_key

        event = self._create_event({
            "username": "test_user",
            "email": "test@example.com"
        })
        context = self._create_context()

        # --- 実行 ---
        issutance_request_handler(event, context)

        # --- 検証 ---
        mock_user.assert_called_once_with("test_user", "test@example.com")
        mock_service.request_issuance.assert_called_once_with(mock_user.return_value)
        mock_builder.success.assert_called_once_with({"status": "REQUESTED"})

    @patch("usage_key.main.logger")
    @patch("usage_key.main.ApiResponseBuilder")
    @patch("usage_key.main.User")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_success_with_dict_body(
        self, mock_context, mock_user, mock_builder, mock_logger
    ):
        """正常系: bodyが辞書の場合に正しく処理されること"""
        # --- 準備 ---
        mock_service = mock_context.usage_key_service
        mock_usage_key = MagicMock()
        mock_usage_key.status = "PENDING"
        mock_service.request_issuance.return_value = mock_usage_key

        event = self._create_event({
            "username": "test_user_dict",
            "email": "test_dict@example.com"
        }, is_json_string=False)
        context = self._create_context()

        issutance_request_handler(event, context)

        mock_user.assert_called_once_with("test_user_dict", "test_dict@example.com")
        mock_service.request_issuance.assert_called_once_with(mock_user.return_value)
        mock_builder.success.assert_called_once_with({"status": "PENDING"})

    @patch("usage_key.main.logger")
    @patch("usage_key.main.ApiResponseBuilder")
    @patch("usage_key.main.User")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_bad_request_no_username(
        self, mock_context, mock_user, mock_builder, mock_logger
    ):
        """異常系: usernameが欠落している場合にBadRequestを返すこと"""
        event = self._create_event({"email": "test@example.com"})
        context = self._create_context()

        issutance_request_handler(event, context)

        mock_builder.bad_request.assert_called_once_with("Invalid 'username' parameter")
        mock_context.usage_key_service.request_issuance.assert_not_called()
        mock_logger.exception.assert_called_once()

    @patch("usage_key.main.logger")
    @patch("usage_key.main.ApiResponseBuilder")
    @patch("usage_key.main.User")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_bad_request_no_email(
        self, mock_context, mock_user, mock_builder, mock_logger
    ):
        """異常系: emailが欠落している場合にBadRequestを返すこと"""
        event = self._create_event({"username": "test_user"})
        context = self._create_context()

        issutance_request_handler(event, context)

        mock_builder.bad_request.assert_called_once_with("Invalid 'email' parameter")
        mock_context.usage_key_service.request_issuance.assert_not_called()
        mock_logger.exception.assert_called_once()

    @patch("usage_key.main.logger")
    @patch("usage_key.main.ApiResponseBuilder")
    @patch("usage_key.main.User")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_internal_server_error(
        self, mock_context, mock_user, mock_builder, mock_logger
    ):
        """異常系: 予期せぬエラーが発生した場合にInternalServerErrorを返すこと"""
        mock_service = mock_context.usage_key_service
        mock_service.request_issuance.side_effect = Exception("Something went wrong")

        event = self._create_event({"username": "test_user", "email": "test@example.com"})
        context = self._create_context()

        issutance_request_handler(event, context)

        mock_builder.internal_server_error.assert_called_once_with("An internal server error occurred")
        mock_logger.exception.assert_called_once()


# テスト実行時に環境変数を設定
@patch.dict(os.environ, {"PARAMETER_PATH_PREFIX": "/test/prefix/"})
class TestCreateUsageKeyHandler(unittest.TestCase):
    """create_usage_key_handlerのテストクラス"""

    @patch("usage_key.main.logger")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_success(self, mock_context, mock_logger):
        """正常系: 正しいUsageKeyIdが渡された場合に正しく処理されること"""
        event = {"UsageKeyId": "key-12345"}
        response = create_usage_key_handler(event, MagicMock())
        mock_context.usage_key_service.create_new_usage_key.assert_called_once_with("key-12345")
        self.assertEqual(response, {"StatusCode": 200})

    @patch("usage_key.main.logger")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_bad_request_no_usage_key_id(self, mock_context, mock_logger):
        """異常系: UsageKeyIdが欠落している場合にStatusCode 400を返すこと"""
        response = create_usage_key_handler({}, MagicMock())
        self.assertEqual(response, {"StatusCode": 400})
        mock_context.usage_key_service.create_new_usage_key.assert_not_called()
        mock_logger.exception.assert_called_once()

    @patch("usage_key.main.logger")
    @patch("usage_key.main.usageKeyServiceContext")
    def test_internal_server_error(self, mock_context, mock_logger):
        """異常系: 予期せぬエラーが発生した場合にStatusCode 500を返すこと"""
        mock_service = mock_context.usage_key_service
        mock_service.create_new_usage_key.side_effect = Exception("DB connection failed")
        response = create_usage_key_handler({"UsageKeyId": "key-12345"}, MagicMock())
        self.assertEqual(response, {"StatusCode": 500})
        mock_logger.exception.assert_called_once()
