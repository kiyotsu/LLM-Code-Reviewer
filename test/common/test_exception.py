import unittest
from botocore.exceptions import ClientError

from common.exception import RequestParameterError, Boto3Exception


class TestRequestParameterError(unittest.TestCase):
    """RequestParameterErrorのテストクラス"""

    def test_init(self):
        """正常系: __init__でメッセージとパラメータ名が正しく設定されることをテスト"""
        param_name = "test_param"
        message = "This is a test message"
        error = RequestParameterError(message, param_name)
        self.assertEqual(error.parameter_name, param_name)
        self.assertEqual(str(error), message)

    def test_not_found(self):
        """正常系: not_foundクラスメソッドが正しい例外を生成することをテスト"""
        param_name = "user_id"
        error = RequestParameterError.not_found(param_name)
        self.assertIsInstance(error, RequestParameterError)
        self.assertEqual(error.parameter_name, param_name)
        self.assertEqual(str(error), f"必須パラメータ '{param_name}' が見つかりません。")

    def test_invalid_format(self):
        """正常系: invalid_formatクラスメソッドが正しい例外を生成することをテスト"""
        param_name = "email"
        reason = "not an email address"
        error = RequestParameterError.invalid_format(param_name, reason)
        self.assertIsInstance(error, RequestParameterError)
        self.assertEqual(error.parameter_name, param_name)
        self.assertEqual(str(error), f"パラメータ '{param_name}' のフォーマットが不正です。理由: {reason}")


class TestBoto3Exception(unittest.TestCase):
    """Boto3Exceptionのテストクラス"""

    def test_reason_with_explicit_reason(self):
        """正常系: reasonが明示的に指定された場合に、そのreasonが返されることをテスト"""
        error = Boto3Exception(service="s3", reason="CustomReason")
        self.assertEqual(error.reason, "CustomReason")

    def test_reason_with_client_error_cause(self):
        """正常系: 原因例外(ClientError)が設定されている場合に、そのエラーコードがreasonとして返されることをテスト"""
        client_error = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': '...'}, 'ResponseMetadata': {}},
            operation_name='GetObject'
        )
        try:
            raise Boto3Exception(service="s3") from client_error
        except Boto3Exception as e:
            self.assertEqual(e.reason, "AccessDenied")

    def test_reason_with_no_cause_or_reason(self):
        """正常系: reasonも原因例外も指定されていない場合に'UnknownError'が返されることをテスト"""
        error = Boto3Exception(service="s3")
        self.assertEqual(error.reason, "UnknownError")

    def test_reason_with_non_client_error_cause(self):
        """正常系: 原因例外がClientErrorでない場合に'UnknownError'が返されることをテスト"""
        try:
            raise Boto3Exception(service="s3") from ValueError("some other error")
        except Boto3Exception as e:
            self.assertEqual(e.reason, "UnknownError")

    def test_operation_name_with_client_error_cause(self):
        """正常系: 原因例外(ClientError)が設定されている場合に、そのオペレーション名が返されることをテスト"""
        client_error = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': '...'}, 'ResponseMetadata': {}},
            operation_name='GetObject'
        )
        try:
            raise Boto3Exception(service="s3") from client_error
        except Boto3Exception as e:
            self.assertEqual(e.operation_name, "GetObject")

    def test_operation_name_with_no_cause(self):
        """正常系: 原因例外が指定されていない場合に'UnknownOpertaion'が返されることをテスト"""
        error = Boto3Exception(service="s3")
        self.assertEqual(error.operation_name, "UnknownOpertaion")

    def test_str_representation(self):
        """正常系: __str__が正しいフォーマットの文字列を返すことをテスト"""
        error = Boto3Exception(service="lambda", reason="Timeout")
        expected_str = "AWSサービス 'lambda' のオペレーション 'UnknownOpertaion' でエラーが発生しました。原因: Timeout"
        self.assertEqual(str(error), expected_str)
