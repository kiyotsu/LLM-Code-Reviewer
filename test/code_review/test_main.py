import base64
import json
import unittest
from unittest.mock import MagicMock, patch

from code_review.main import code_review_handler


class TestCodeReviewHandler(unittest.TestCase):
    """code_review_handlerのテストクラス"""

    def _create_event(self, body):
        """テスト用のAPI Gatewayイベントを作成するヘルパーメソッド"""
        return {"body": json.dumps(body)}

    def _create_context(self):
        """テスト用のLambdaコンテキストを作成するヘルパーメソッド"""
        context = MagicMock()
        context.aws_request_id = "test-request-id"
        return context

    @patch("code_review.main.container")
    def test_handler_success(self, mock_container):
        """正常系: 正しいリクエストでコードレビューが成功し、200レスポンスが返ることをテスト"""
        mock_service = mock_container.code_review_service
        mock_review_result = {"review_result": "OK", "review_points": []}
        mock_service.excute_review.return_value = mock_review_result

        source_code = "print('hello')"
        source_base64 = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
        event = self._create_event({
            "source_base64": source_base64,
            "language": "python"
        })
        context = self._create_context()

        response = code_review_handler(event, context)

        mock_service.excute_review.assert_called_once_with(source_code, "python")
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), mock_review_result)

    @patch("code_review.main.container")
    def test_handler_body_is_dict(self, mock_container):
        """正常系: event['body']が文字列化されていない辞書の場合でも正しく動作することをテスト"""
        mock_service = mock_container.code_review_service
        mock_review_result = {"review_result": "OK"}
        mock_service.excute_review.return_value = mock_review_result

        source_code = "print('hello')"
        source_base64 = base64.b64encode(source_code.encode('utf-8')).decode('utf-8')
        event = {
            "body": {
                "source_base64": source_base64,
                "language": "python"
            }
        }
        context = self._create_context()

        response = code_review_handler(event, context)

        mock_service.excute_review.assert_called_once_with(source_code, "python")
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), mock_review_result)

    @patch("code_review.main.container")
    def test_handler_no_source_base64(self, mock_container):
        """異常系: source_base64がない場合に400エラーが返ることをテスト"""
        event = self._create_event({"language": "python"})
        context = self._create_context()

        response = code_review_handler(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid 'source_base64' parameter", response["body"])
        mock_container.code_review_service.excute_review.assert_not_called()

    @patch("code_review.main.container")
    def test_handler_no_language(self, mock_container):
        """異常系: languageがない場合に400エラーが返ることをテスト"""
        source_base64 = base64.b64encode(b"test").decode('utf-8')
        event = self._create_event({"source_base64": source_base64})
        context = self._create_context()

        response = code_review_handler(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid 'language' parameter", response["body"])
        mock_container.code_review_service.excute_review.assert_not_called()

    @patch("code_review.main.container")
    def test_handler_invalid_base64(self, mock_container):
        """異常系: source_base64が不正な場合に400エラーが返ることをテスト"""
        event = self._create_event({
            "source_base64": "not-a-base64-string-!",
            "language": "python"
        })
        context = self._create_context()

        response = code_review_handler(event, context)

        self.assertEqual(response["statusCode"], 400)
        self.assertIn("Invalid 'source_base64' parameter", response["body"])
        mock_container.code_review_service.excute_review.assert_not_called()

    @patch("code_review.main.logger")
    @patch("code_review.main.container")
    def test_handler_internal_server_error(self, mock_container, mock_logger):
        """異常系: 予期せぬエラーが発生した場合に500エラーが返ることをテスト"""
        mock_service = mock_container.code_review_service
        mock_service.excute_review.side_effect = Exception("Something went wrong")
        source_base64 = base64.b64encode(b"test").decode('utf-8')
        event = self._create_event({"source_base64": source_base64, "language": "python"})
        context = self._create_context()

        response = code_review_handler(event, context)

        self.assertEqual(response["statusCode"], 500)
        self.assertIn("An internal server error occurred", response["body"])
        mock_logger.exception.assert_called_once()
