import unittest

from common.boto3_helper import SesDestination


class TestSesDestination(unittest.TestCase):
    """SesDestinationのテストクラス"""

    def test_init(self):
        """正常系: __init__で各プロパティが正しく設定されることをテスト"""
        tos = ["to@example.com"]
        ccs = ["cc@example.com"]
        bccs = ["bcc@example.com"]

        # すべての引数を指定
        dest_all = SesDestination(tos=tos, ccs=ccs, bccs=bccs)
        self.assertEqual(dest_all.tos, tos)
        self.assertEqual(dest_all.ccs, ccs)
        self.assertEqual(dest_all.bccs, bccs)

        # オプション引数を指定しない
        dest_tos_only = SesDestination(tos=tos)
        self.assertEqual(dest_tos_only.tos, tos)
        self.assertIsNone(dest_tos_only.ccs)
        self.assertIsNone(dest_tos_only.bccs)

    def test_to_service_format_with_tos_only(self):
        """正常系: ToSのみ指定した場合に正しいSESフォーマットが返されることをテスト"""
        tos = ["to1@example.com", "to2@example.com"]
        destination = SesDestination(tos=tos)
        expected_format = {"ToAddresses": tos}
        self.assertEqual(destination.to_service_format(), expected_format)

    def test_to_service_format_with_tos_and_ccs(self):
        """正常系: ToSとCCsを指定した場合に正しいSESフォーマットが返されることをテスト"""
        tos = ["to@example.com"]
        ccs = ["cc1@example.com", "cc2@example.com"]
        destination = SesDestination(tos=tos, ccs=ccs)
        expected_format = {"ToAddresses": tos, "CcAddresses": ccs}
        self.assertEqual(destination.to_service_format(), expected_format)

    def test_to_service_format_with_all_fields(self):
        """正常系: すべてのフィールドを指定した場合に正しいSESフォーマットが返されることをテスト"""
        tos = ["to@example.com"]
        ccs = ["cc@example.com"]
        bccs = ["bcc@example.com"]
        destination = SesDestination(tos=tos, ccs=ccs, bccs=bccs)
        expected_format = {
            "ToAddresses": tos,
            "CcAddresses": ccs,
            "BccAddresses": bccs,
        }
        self.assertEqual(destination.to_service_format(), expected_format)
