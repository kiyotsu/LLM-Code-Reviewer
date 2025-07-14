import json
import unittest

from common.response import ApiResponseBuilder


class TestApiResponseBuilder(unittest.TestCase):
    """ApiResponseBuilderのテストクラス"""

    def test_build_default(self):
        """正常系: デフォルト値でレスポンスが構築されることをテスト"""
        builder = ApiResponseBuilder()
        response = builder.build()
        expected = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": ""
        }
        self.assertEqual(response, expected)

    def test_with_body_json(self):
        """正常系: JSONボディが正しく設定され、文字列化されることをテスト"""
        body_dict = {"message": "success", "data": [1, 2]}
        response = ApiResponseBuilder().with_body(body_dict).build()
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(json.loads(response["body"]), body_dict)

    def test_with_body_non_json_content_type(self):
        """正常系: Content-TypeがJSONでない場合、ボディが単純な文字列になることをテスト"""
        body_text = "Hello, World!"
        response = ApiResponseBuilder() \
            .with_content_type("text/plain") \
            .with_body(body_text) \
            .build()
        self.assertEqual(response["body"], body_text)

    def test_with_headers(self):
        """正常系: ヘッダーが追加・上書きされることをテスト"""
        headers = {"X-Custom-Header": "MyValue", "Content-Type": "text/xml"}
        response = ApiResponseBuilder().with_headers(headers).build()
        expected_headers = {
            "Content-Type": "text/xml",  # Overwritten
            "X-Custom-Header": "MyValue"  # Added
        }
        self.assertEqual(response["headers"], expected_headers)

    def test_with_content_type(self):
        """正常系: Content-Typeが正しく設定されることをテスト"""
        response = ApiResponseBuilder().with_content_type("application/xml").build()
        self.assertEqual(response["headers"]["Content-Type"], "application/xml")

    def test_chaining_methods(self):
        """正常系: メソッドチェーンが正しく機能することをテスト"""
        body = {"data": "test"}
        headers = {"Cache-Control": "no-cache"}
        response = ApiResponseBuilder(201) \
            .with_body(body) \
            .with_headers(headers) \
            .build()

        self.assertEqual(response["statusCode"], 201)
        self.assertEqual(json.loads(response["body"]), body)
        self.assertIn("Cache-Control", response["headers"])
        self.assertEqual(response["headers"]["Cache-Control"], "no-cache")
        self.assertIn("Content-Type", response["headers"])
        self.assertEqual(response["headers"]["Content-Type"], "application/json")

    def test_success_static_method(self):
        """正常系: success静的メソッドが正しいレスポンスを生成することをテスト"""
        body = {"status": "ok"}
        response = ApiResponseBuilder.success(body)
        expected = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps(body, ensure_ascii=False)
        }
        self.assertEqual(response, expected)

        # ステータスコードを指定した場合
        response_201 = ApiResponseBuilder.success(body, status_code=201)
        self.assertEqual(response_201["statusCode"], 201)

    def test_error_static_method(self):
        """正常系: error静的メソッドが正しいエラーレスポンスを生成することをテスト"""
        message = "Something went wrong"
        status_code = 502
        response = ApiResponseBuilder.error(message, status_code)
        expected_body = {"message": message}
        self.assertEqual(response["statusCode"], status_code)
        self.assertEqual(json.loads(response["body"]), expected_body)

    def test_bad_request_static_method(self):
        """正常系: bad_request静的メソッドが400エラーレスポンスを生成することをテスト"""
        message = "Invalid parameter"
        response = ApiResponseBuilder.bad_request(message)
        expected_body = {"message": message}
        self.assertEqual(response["statusCode"], 400)
        self.assertEqual(json.loads(response["body"]), expected_body)

    def test_internal_server_error_static_method(self):
        """正常系: internal_server_error静的メソッドが500エラーレスポンスを生成することをテスト"""
        response_default = ApiResponseBuilder.internal_server_error()
        expected_body_default = {"message": "An internal server error occurred."}
        self.assertEqual(response_default["statusCode"], 500)
        self.assertEqual(json.loads(response_default["body"]), expected_body_default)

    def test_json_dumps_with_non_ascii(self):
        """正常系: 日本語を含むJSONボディがensure_ascii=Falseでダンプされることをテスト"""
        body_dict = {"message": "成功"}
        response = ApiResponseBuilder().with_body(body_dict).build()
        self.assertEqual(response["body"], '{"message": "成功"}')
