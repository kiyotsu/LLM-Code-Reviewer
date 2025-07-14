import os
import unittest
from unittest.mock import MagicMock, PropertyMock, patch

from botocore.exceptions import ClientError

from usage_key.usage_key import (
    ApiGatewayKeyManager,
    UsageKeyFromDynamoDB,
    SsmAutomationManager,
    SesMailSender,
    UsageKeyService,
    UsageKeyServiceContext,
)
from usage_key.domain import (
    UsageKey, User, KeyStatus,
    IApiKeyManager,
    IUsageKeyRepository,
    IAutomationManager,
    IMailSender,
)
from common.exception import ApplicationException, Boto3Exception


class TestApiGatewayKeyManager(unittest.TestCase):
    """ApiGatewayKeyManagerのテストクラス"""

    def test_create_key(self):
        """正常系: APIキーが作成され、Usage Planに紐付けられることをテスト"""
        mock_client = MagicMock()
        mock_client.create_api_key.return_value = {"id": "key-id", "value": "key-value"}
        manager = ApiGatewayKeyManager(mock_client, "plan-id")

        result = manager.create_key("test-key", "description")

        mock_client.create_api_key.assert_called_once_with(
            name="test-key", description="description", enabled=True
        )
        mock_client.create_usage_plan_key.assert_called_once_with(
            usagePlanId="plan-id", keyId="key-id", keyType="API_KEY"
        )
        self.assertEqual(result, {"id": "key-id", "value": "key-value"})


class TestUsageKeyFromDynamoDB(unittest.TestCase):
    """UsageKeyFromDynamoDBのテストクラス"""

    def setUp(self):
        self.mock_client = MagicMock()
        self.repo = UsageKeyFromDynamoDB(self.mock_client, "test-table")

    def test_save_key(self):
        """正常系: UsageKeyが正しくDynamoDBに保存されることをテスト"""
        user = User("test-user", "test@example.com")
        usage_key = UsageKey("usage-id", "api-id", user, KeyStatus.CREATED)

        with patch("usage_key.usage_key.datetime") as mock_datetime:
            mock_datetime.now.return_value.isoformat.return_value = "2023-01-01T00:00:00"
            self.repo.save_key(usage_key)

        self.mock_client.put_item.assert_called_once()
        call_args = self.mock_client.put_item.call_args[1]
        self.assertEqual(call_args["TableName"], "test-table")
        self.assertEqual(call_args["Item"]["usage_key_id"]["S"], "usage-id")
        self.assertEqual(call_args["Item"]["api_key_id"]["S"], "api-id")
        self.assertEqual(call_args["Item"]["username"]["S"], "test-user")
        self.assertEqual(call_args["Item"]["email"]["S"], "test@example.com")
        self.assertEqual(call_args["Item"]["status"]["S"], "CREATED")
        self.assertEqual(call_args["Item"]["saved_at"]["S"], "2023-01-01T00:00:00")

    def test_get_key_found(self):
        """正常系: キーが見つかった場合にUsageKeyオブジェクトが返されることをテスト"""
        mock_item = {
            "usage_key_id": {"S": "usage-id"},
            "api_key_id": {"S": "api-id"},
            "username": {"S": "test-user"},
            "email": {"S": "test@example.com"},
            "status": {"S": "PENDING"},
        }
        self.mock_client.get_item.return_value = {"Item": mock_item}

        result = self.repo.get_key("usage-id")

        self.assertIsInstance(result, UsageKey)
        self.assertEqual(result.usage_key_id, "usage-id")
        self.assertEqual(result.user.name, "test-user")
        self.assertEqual(result.status, KeyStatus.PENDING)

    def test_get_key_not_found(self):
        """正常系: キーが見つからない場合にNoneが返されることをテスト"""
        self.mock_client.get_item.return_value = {}
        result = self.repo.get_key("not-found-id")
        self.assertIsNone(result)

    def test_delete_key(self):
        """正常系: キーが正しく削除されることをテスト"""
        self.repo.delete_key("usage-id")
        self.mock_client.delete_item.assert_called_once_with(
            TableName="test-table", Key={"usage_key_id": {"S": "usage-id"}}
        )


class TestSsmAutomationManager(unittest.TestCase):
    """SsmAutomationManagerのテストクラス"""

    def test_start_approval_workflow(self):
        """正常系: SSM Automationが正しいパラメータで開始されることをテスト"""
        mock_client = MagicMock()
        manager = SsmAutomationManager(mock_client, "doc-name")
        params = {"Key1": "Value1", "Key2": "Value2"}

        manager.start_approval_workflow(params)

        expected_params = {"Key1": ["Value1"], "Key2": ["Value2"]}
        mock_client.start_automation_execution.assert_called_once_with(
            DocumentName="doc-name", Parameters=expected_params
        )


class TestSesMailSender(unittest.TestCase):
    """SesMailSenderのテストクラス"""

    def setUp(self):
        self.mock_client = MagicMock()
        self.sender = SesMailSender(self.mock_client, "from@example.com")

    def test_send_email_success(self):
        """正常系: メールが正常に送信されることをテスト"""
        self.mock_client.send_email.return_value = {"MessageId": "msg-id"}
        to, subject, text, html = "to@example.com", "Subject", "Text", "Html"

        message_id = self.sender.send_email(to, subject, text, html)

        self.assertEqual(message_id, "msg-id")
        self.mock_client.send_email.assert_called_once()
        call_args = self.mock_client.send_email.call_args[1]
        self.assertEqual(call_args["Source"], "from@example.com")
        self.assertEqual(call_args["Destination"], {"ToAddresses": [to]})

    def test_send_email_with_reply_tos(self):
        """正常系: ReplyToが指定された場合に正しく引数が設定されることをテスト"""
        self.mock_client.send_email.return_value = {"MessageId": "msg-id"}
        to, subject, text, html, reply_tos = "to@example.com", "S", "T", "H", ["reply@example.com"]

        self.sender.send_email(to, subject, text, html, reply_tos)

        call_args = self.mock_client.send_email.call_args[1]
        self.assertEqual(call_args["ReplyToAddresses"], reply_tos)

    def test_send_email_client_error(self):
        """異常系: ClientErrorが発生した場合に例外が再送出されることをテスト"""
        self.mock_client.send_email.side_effect = ClientError({}, "SendEmail")
        with self.assertRaises(ClientError):
            self.sender.send_email("to@example.com", "S", "T", "H")


class TestUsageKeyService(unittest.TestCase):
    """UsageKeyServiceのテストクラス"""

    def setUp(self):
        self.mock_api_key_manager = MagicMock(spec=IApiKeyManager)
        self.mock_repo = MagicMock(spec=IUsageKeyRepository)
        self.mock_automation = MagicMock(spec=IAutomationManager)
        self.mock_mailer = MagicMock(spec=IMailSender)
        self.service = UsageKeyService(
            self.mock_api_key_manager,
            self.mock_repo,
            self.mock_automation,
            self.mock_mailer,
        )
        self.user = User("test-user", "test@example.com")

    def test_request_issuance_new(self):
        """正常系(新規): 利用キー発行リクエストが正常に処理される"""
        # --- 準備 ---
        self.mock_repo.get_key.return_value = None

        # --- 実行 ---
        with patch("usage_key.usage_key.uuid.uuid4", return_value="new-uuid"):
            result = self.service.request_issuance(self.user)

        # --- 検証 ---
        self.mock_repo.get_key.assert_called_once_with(self.user.email)
        self.mock_repo.save_key.assert_called_once()
        saved_key = self.mock_repo.save_key.call_args[0][0]
        self.assertEqual(saved_key.usage_key_id, "new-uuid")
        self.assertEqual(saved_key.status, KeyStatus.PENDING)

        self.mock_automation.start_approval_workflow.assert_called_once_with(
            {
                "UsageKeyId": "new-uuid",
                "Username": self.user.name,
                "Email": self.user.email,
            }
        )
        self.assertEqual(result, saved_key)

    def test_request_issuance_existing(self):
        """正常系(既存): 既にキーが存在する場合、そのまま返す"""
        existing_key = UsageKey("exist-id", "api-id", self.user, KeyStatus.CREATED)
        self.mock_repo.get_key.return_value = existing_key

        result = self.service.request_issuance(self.user)

        self.mock_repo.get_key.assert_called_once_with(self.user.email)
        self.mock_repo.save_key.assert_not_called()
        self.mock_automation.start_approval_workflow.assert_not_called()
        self.assertEqual(result, existing_key)

    def test_request_issuance_dynamodb_error(self):
        """異常系: DynamoDBへの保存でエラーが発生した場合"""
        self.mock_repo.get_key.return_value = None
        self.mock_repo.save_key.side_effect = ClientError({}, "PutItem")

        with self.assertRaises(Boto3Exception) as cm:
            self.service.request_issuance(self.user)
        self.assertEqual(cm.exception.service, "dynamodb")

    def test_request_issuance_ssm_error(self):
        """異常系: SSM Automationの開始でエラーが発生した場合、ロールバックされる"""
        self.mock_repo.get_key.return_value = None
        self.mock_automation.start_approval_workflow.side_effect = ClientError({}, "StartAutomationExecution")

        with self.assertRaises(Boto3Exception) as cm, \
             patch("usage_key.usage_key.uuid.uuid4", return_value="new-uuid"):
            self.service.request_issuance(self.user)

        self.assertEqual(cm.exception.service, "ssm")
        self.mock_repo.delete_key.assert_called_once_with("new-uuid")

    def test_create_new_usage_key_success(self):
        """正常系: 新しい利用キーが正常に作成・通知される"""
        pending_key = UsageKey("pending-id", "", self.user, KeyStatus.PENDING)
        self.mock_repo.get_key.return_value = pending_key
        self.mock_api_key_manager.create_key.return_value = {"id": "api-id-123", "value": "api-value-xyz"}

        result = self.service.create_new_usage_key("pending-id")

        self.mock_repo.get_key.assert_called_once_with("pending-id")
        self.mock_api_key_manager.create_key.assert_called_once()
        self.mock_repo.save_key.assert_called_once()
        saved_key = self.mock_repo.save_key.call_args[0][0]
        self.assertEqual(saved_key.api_key_id, "api-id-123")
        self.assertEqual(saved_key.status, KeyStatus.CREATED)

        self.mock_mailer.send_email.assert_called_once_with(
            to_address=self.user.email,
            subject="[コードレビューAPI]利用キーを発行しました",
            text="api-value-xyz",
            html="api-value-xyz",
        )
        self.assertEqual(result, saved_key)

    def test_create_new_usage_key_not_pending(self):
        """異常系: 対象キーがPENDINGでない場合"""
        created_key = UsageKey("created-id", "api-id", self.user, KeyStatus.CREATED)
        self.mock_repo.get_key.return_value = created_key

        with self.assertRaisesRegex(ApplicationException, "発行リクエストを行ってください。"):
            self.service.create_new_usage_key("created-id")

    def test_create_new_usage_key_not_found(self):
        """異常系: 対象キーが存在しない場合"""
        self.mock_repo.get_key.return_value = None
        with self.assertRaisesRegex(ApplicationException, "発行リクエストを行ってください。"):
            self.service.create_new_usage_key("not-found-id")

    def test_create_new_usage_key_apigw_error(self):
        """異常系: API Gatewayでのキー作成エラー"""
        pending_key = UsageKey("pending-id", "", self.user, KeyStatus.PENDING)
        self.mock_repo.get_key.return_value = pending_key
        self.mock_api_key_manager.create_key.side_effect = ClientError({}, "CreateApiKey")

        with self.assertRaises(Boto3Exception) as cm:
            self.service.create_new_usage_key("pending-id")
        self.assertEqual(cm.exception.service, "apigateway")

    def test_create_new_usage_key_dynamodb_error(self):
        """異常系: DynamoDBへの保存エラー"""
        pending_key = UsageKey("pending-id", "", self.user, KeyStatus.PENDING)
        self.mock_repo.get_key.return_value = pending_key
        self.mock_api_key_manager.create_key.return_value = {"id": "api-id", "value": "val"}
        self.mock_repo.save_key.side_effect = ClientError({}, "PutItem")

        with self.assertRaises(Boto3Exception) as cm:
            self.service.create_new_usage_key("pending-id")
        self.assertEqual(cm.exception.service, "dynamodb")

    def test_create_new_usage_key_ses_error(self):
        """異常系: SESでのメール送信エラー"""
        pending_key = UsageKey("pending-id", "", self.user, KeyStatus.PENDING)
        self.mock_repo.get_key.return_value = pending_key
        self.mock_api_key_manager.create_key.return_value = {"id": "api-id", "value": "val"}
        self.mock_mailer.send_email.side_effect = ClientError({}, "SendEmail")

        with self.assertRaises(Boto3Exception) as cm:
            self.service.create_new_usage_key("pending-id")
        self.assertEqual(cm.exception.service, "ses")


@patch.dict(os.environ, {"PARAMETER_PATH_PREFIX": "/test/prefix/"})
class TestUsageKeyServiceContext(unittest.TestCase):
    """UsageKeyServiceContextのテストクラス"""

    def setUp(self):
        """lru_cacheをクリアしてテスト間の独立性を保つ"""
        # プロパティはlru_cacheでデコレートされているため、fget経由でキャッシュをクリア
        for name, member in UsageKeyServiceContext.__dict__.items():
            if isinstance(member, property) and hasattr(member.fget, 'cache_clear'):
                member.fget.cache_clear()
        self.context = UsageKeyServiceContext()

    @patch("usage_key.usage_key.boto3.client")
    def test_clients_cached(self, mock_boto3_client):
        """各boto3クライアントがキャッシュされることをテスト"""
        clients = ["ssm", "apigateway", "dynamodb", "ses"]
        for client_name in clients:
            client1 = getattr(self.context, f"{client_name}_client")
            client2 = getattr(self.context, f"{client_name}_client")
            self.assertIs(client1, client2)

        self.assertEqual(mock_boto3_client.call_count, len(clients))
        mock_boto3_client.assert_any_call("ssm")
        mock_boto3_client.assert_any_call("apigateway")

    @patch("usage_key.usage_key.SsmConfigLoader")
    def test_ssm_config_loader_cached(self, MockSsmConfigLoader):
        """SsmConfigLoaderがキャッシュされることをテスト"""
        with patch.object(UsageKeyServiceContext, 'ssm_client', new_callable=PropertyMock) as mock_ssm_client:
            loader1 = self.context.ssm_config_loader
            loader2 = self.context.ssm_config_loader
            self.assertIs(loader1, loader2)
            MockSsmConfigLoader.assert_called_once_with(mock_ssm_client.return_value, "/test/prefix/")

    def test_configs_cached(self):
        """各configプロパティがキャッシュされることをテスト"""
        mock_loader_instance = MagicMock()
        mock_loader_instance.load_config.side_effect = lambda x: {f"{x}_key": f"{x}_value"}

        with patch.object(UsageKeyServiceContext, 'ssm_config_loader', new_callable=PropertyMock) as mock_loader_prop:
            mock_loader_prop.return_value = mock_loader_instance

            configs = ["ssm", "apigateway", "dynamodb", "ses"]
            for config_name in configs:
                config1 = getattr(self.context, f"{config_name}_config")
                config2 = getattr(self.context, f"{config_name}_config")
                self.assertIs(config1, config2)
                self.assertEqual(config1, {f"{config_name}_key": f"{config_name}_value"})

            self.assertEqual(mock_loader_instance.load_config.call_count, len(configs))
            mock_loader_instance.load_config.assert_any_call("apigateway")

    @patch("usage_key.usage_key.ApiGatewayKeyManager")
    @patch("usage_key.usage_key.UsageKeyFromDynamoDB")
    @patch("usage_key.usage_key.SsmAutomationManager")
    @patch("usage_key.usage_key.SesMailSender")
    def test_managers_and_repository_instantiation(
        self,
        MockSesMailSender,
        MockSsmAutomationManager,
        MockUsageKeyFromDynamoDB,
        MockApiGatewayKeyManager,
    ):
        """各Manager/Repositoryが正しくインスタンス化されることをテスト"""
        # --- 準備 ---
        with patch.object(UsageKeyServiceContext, 'apigateway_client', new_callable=PropertyMock) as mock_apigw_client, \
             patch.object(UsageKeyServiceContext, 'apigateway_config', new_callable=PropertyMock, return_value={"UsagePlanId": "plan-123"}) as mock_apigw_config, \
             patch.object(UsageKeyServiceContext, 'dynamodb_client', new_callable=PropertyMock) as mock_ddb_client, \
             patch.object(UsageKeyServiceContext, 'dynamodb_config', new_callable=PropertyMock, return_value={"UsageKeyTableName": "table-123"}) as mock_ddb_config, \
             patch.object(UsageKeyServiceContext, 'ssm_client', new_callable=PropertyMock) as mock_ssm_client, \
             patch.object(UsageKeyServiceContext, 'ssm_config', new_callable=PropertyMock, return_value={"AutomationDocumentName": "doc-123"}) as mock_ssm_config, \
             patch.object(UsageKeyServiceContext, 'ses_client', new_callable=PropertyMock) as mock_ses_client, \
             patch.object(UsageKeyServiceContext, 'ses_config', new_callable=PropertyMock, return_value={"FromMailAddress": "from@example.com"}) as mock_ses_config:

            # --- 実行 & 検証 ---
            self.assertIsInstance(self.context.api_key_manager, MagicMock)
            self.assertIsInstance(self.context.usage_key_repository, MagicMock)
            self.assertIsInstance(self.context.automation_manager, MagicMock)
            self.assertIsInstance(self.context.mail_sender, MagicMock)

            MockApiGatewayKeyManager.assert_called_once_with(mock_apigw_client.return_value, "plan-123")
            MockUsageKeyFromDynamoDB.assert_called_once_with(mock_ddb_client.return_value, "table-123")
            MockSsmAutomationManager.assert_called_once_with(mock_ssm_client.return_value, "doc-123")
            MockSesMailSender.assert_called_once_with(mock_ses_client.return_value, "from@example.com")

    @patch("usage_key.usage_key.UsageKeyService")
    def test_usage_key_service_cached(self, MockUsageKeyService):
        """usage_key_serviceがキャッシュされ、正しい依存関係で初期化されることをテスト"""
        with patch.object(UsageKeyServiceContext, 'api_key_manager', new_callable=PropertyMock) as mock_api_mgr, \
             patch.object(UsageKeyServiceContext, 'usage_key_repository', new_callable=PropertyMock) as mock_repo, \
             patch.object(UsageKeyServiceContext, 'automation_manager', new_callable=PropertyMock) as mock_auto_mgr, \
             patch.object(UsageKeyServiceContext, 'mail_sender', new_callable=PropertyMock) as mock_mailer:

            service1 = self.context.usage_key_service
            service2 = self.context.usage_key_service

            self.assertIs(service1, service2)
            MockUsageKeyService.assert_called_once_with(
                mock_api_mgr.return_value,
                mock_repo.return_value,
                mock_auto_mgr.return_value,
                mock_mailer.return_value
            )
