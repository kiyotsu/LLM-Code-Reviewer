import os
import uuid
import logging
from functools import lru_cache
from datetime import datetime
from typing import Dict, Optional

import boto3
from botocore.exceptions import ClientError

from usage_key.domain import IApiKeyManager, IUsageKeyRepository, IAutomationManager, IMailSender, UsageKey, User, KeyStatus
from common.config import SsmConfigLoader
from common.exception import ApplicationException, Boto3Exception
from common.boto3_helper import SesDestination


# --- ロガー初期化 ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class ApiGatewayKeyManager(IApiKeyManager):
    """API GatewayのAPIキー操作を担当するクラス"""
    def __init__(
            self,
            apigateway_client: "APIGatewayClient",
            usage_plan_id: str
    ):
        self.apigateway_client = apigateway_client
        self.usage_plan_id = usage_plan_id

    def create_key(self, name: str, description: Optional[str] = None) -> Dict[str, str]:
        """APIキーを作成し、指定されたUsage Planに紐付ける"""
        api_key = self.apigateway_client.create_api_key(
            name=name,
            description=description,
            enabled=True,
        )
        key_id = api_key["id"]
        key_value = api_key["value"]

        self.apigateway_client.create_usage_plan_key(
            usagePlanId=self.usage_plan_id,
            keyId=key_id,
            keyType="API_KEY"
        )
        return {"id": key_id, "value": key_value}


class UsageKeyFromDynamoDB(IUsageKeyRepository):
    """DynamoDBへのUsageKey情報の永続化を担当するクラス"""
    def __init__(self, dynamodb_client: "DynamoDBClient", table_name: str):
        self.dynamodb_client = dynamodb_client
        self.table_name = table_name

    def save_key(self, usage_key: UsageKey):
        """UsageKey情報をDynamoDBに保存する"""
        timestamp = datetime.now().isoformat()
        self.dynamodb_client.put_item(
            TableName=self.table_name,
            Item={
                "usage_key_id": {"S": usage_key.usage_key_id},
                "api_key_id": {"S": usage_key.api_key_id},
                "username":  {"S": usage_key.user.name},
                "email": {"S": usage_key.user.email},
                "status": {"S": usage_key.status},
                "saved_at": {"S": timestamp},
            },
        )

    def get_key(self, key_id: str) -> Optional[UsageKey]:
        """UsageKey情報をDynamoDBから取得する"""
        response = self.dynamodb_client.get_item(
            TableName=self.table_name,
            Key={"usage_key_id": {"S": key_id}},
        )
        item = response.get("Item")
        if not item:
            return None
        return UsageKey(
            usage_key_id=item["usage_key_id"]["S"],
            api_key_id=item["api_key_id"]["S"],
            user=User(
                name=item["username"]["S"],
                email=item["email"]["S"],
            ),
            status=KeyStatus(item["status"]["S"]),
        )

    def delete_key(self, key_id: str):
        """UsageKey情報をDynamoDBから削除する"""
        self.dynamodb_client.delete_item(
            TableName=self.table_name,
            Key={"usage_key_id": {"S": key_id}},
        )

class SsmAutomationManager(IAutomationManager):
    """SSM Automationを使って承認ワークフローを実行するクラス"""
    def __init__(self, ssm_client: "SSMClient", document_name: str):
        self.ssm_client = ssm_client
        self.document_name = document_name

    def start_approval_workflow(self, params: Dict):
        """SSM Automationを開始して承認プロセスをキックする"""
        # --- Key:List[Value]の形式に変換する ----
        parameters = {}
        for key, value in params.items():
            parameters[key] = [value]

        self.ssm_client.start_automation_execution(
            DocumentName=self.document_name,
            Parameters=parameters,
        )

class SesMailSender(IMailSender):
    """Encapsulates functions to send emails with Amazon SES."""

    def __init__(self, ses_client, from_address):
        """
        :param ses_client: A Boto3 Amazon SES client.
        """
        self.ses_client = ses_client
        self.from_address = from_address

    def send_email(self, to_address, subject, text, html, reply_tos=None):
        """
        Sends an email.

        Note: If your account is in the Amazon SES  sandbox, the source and
        destination email accounts must both be verified.

        :param source: The source email account.
        :param destination: The destination email account.
        :param subject: The subject of the email.
        :param text: The plain text version of the body of the email.
        :param html: The HTML version of the body of the email.
        :param reply_tos: Email accounts that will receive a reply if the recipient
                          replies to the message.
        :return: The ID of the message, assigned by Amazon SES.
        """
        send_args = {
            "Source": self.from_address,
            "Destination": SesDestination(tos=[to_address]).to_service_format(),
            "Message": {
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": text}, "Html": {"Data": html}},
            },
        }
        if reply_tos is not None:
            send_args["ReplyToAddresses"] = reply_tos
        try:
            response = self.ses_client.send_email(**send_args)
            message_id = response["MessageId"]
            logger.info(
                "Sent mail %s from %s to %s.", message_id, self.from_address, to_address
            )
        except ClientError:
            logger.exception(
                "Couldn't send mail from %s to %s.", self.from_address, to_address
            )
            raise
        else:
            return message_id


class UsageKeyService:
    """
    利用キー発行のビジネスロジックを実装
    """
    def __init__(
        self,
        api_key_manager: IApiKeyManager,
        usage_key_repository: IUsageKeyRepository,
        automation_manager: IAutomationManager,
        mail_sender : IMailSender,
    ):
        self.api_key_manager = api_key_manager
        self.usage_key_repository = usage_key_repository
        self.automation_manager = automation_manager
        self.mail_sender = mail_sender

    def request_issuance(self, user: User) -> UsageKey:
        """
        利用キーの発行リクエストを受け付け、承認オートメーションを開始する。
        Args:
            user: キーを発行するユーザーの情報
        Returns:
            承認待ち状態のUsageKeyドメインオブジェクト
        """
        logger.info(f"利用キー発行手続きを開始します.... Username={user.name}, Email={user.email}")

        # --- 発行済みのチェック ---
        usage_key: Optional[UsageKey] = self.usage_key_repository.get_key(user.email)
        if usage_key:
            # --- 発行済みであればそのままリターン ---
            logger.info(f"既にキーが存在します。usageKeyId={usage_key.usage_key_id}")
            return usage_key

        try:
            # --- 利用キー仮発行 ---
            pending_key = UsageKey(
                usage_key_id=str(uuid.uuid4()),
                api_key_id="",
                user=user,
                status=KeyStatus.PENDING
            )

            # --- 仮発行した利用キーを永続化 ---
            self.usage_key_repository.save_key(pending_key)
            logger.info(f"仮の利用キーを保存しました。 usageKeyId={pending_key.usage_key_id}")

        except ClientError as error:
            raise Boto3Exception(service="dynamodb") from error

        try:
            # --- 承認用オートメーションを実行 ---
            self.automation_manager.start_approval_workflow(
                {
                    "UsageKeyId": pending_key.usage_key_id,
                    "Username": user.name,
                    "Email": user.email,
                }
            )
            logger.info(f"承認用オートメーションを実行しました。 usageKeyId={pending_key.usage_key_id}")

        except ClientError as error:
            # --- 仮の利用キーを削除 ---
            self.usage_key_repository.delete_key(pending_key.usage_key_id)

            raise Boto3Exception(service="ssm") from error

        return pending_key

    def create_new_usage_key(self, key_id: str) -> UsageKey:
        """
        APIキーを発行し利用キーと紐づけを行う
        Args:
            key_id : 利用キーのID(仮発行済)
        Returns:
            発行され、永続化されたUsageKeyドメインオブジェクト
        """
        logger.info(f"利用キーの作成を開始します.... usageKeyId={key_id}")

        # --- 仮のキーがあるかチェックする ---
        pending_key: Optional[UsageKey] = self.usage_key_repository.get_key(key_id)
        if not pending_key or pending_key.status != KeyStatus.PENDING:
            logger.error(f"発行リクエストを行ってください。usageKeyId={key_id}")
            raise ApplicationException("発行リクエストを行ってください。")

        try:
            # --- APIキーを作成する ---
            key_name = f"{pending_key.usage_key_id}-{pending_key.user.name}"
            api_key = self.api_key_manager.create_key(
                name=key_name,
                description=f"Creaated by LLM Code Reviewer for {pending_key.user.name}({pending_key.user.email})",
            )
            logger.info(f'APIキーを作成しました。 usageKeyId={api_key["id"]}')

        except ClientError as error:
            raise Boto3Exception(service="apigateway") from error

        try:
            # --- 正式な利用キーオブジェクトを作成 ---
            new_usage_key = UsageKey(
                usage_key_id=pending_key.usage_key_id,
                api_key_id=api_key["id"],
                user=pending_key.user,
                status=KeyStatus.CREATED
            )

            # --- 発行情報を永続化 ---
            self.usage_key_repository.save_key(new_usage_key)
            logger.info(f"利用キーを保存しました。 usageKeyId={new_usage_key.usage_key_id}")

        except ClientError as error:
            raise Boto3Exception(service="dynamodb") from error

        try:
            # --- メールで利用キーを通知する ---
            self.mail_sender.send_email(
                to_address=pending_key.user.email,
                subject="[コードレビューAPI]利用キーを発行しました",
                text=f'{api_key["value"]}',
                html=f'{api_key["value"]}',
            )
            logger.info(f"利用キーを通知しました。 usageKeyId={new_usage_key.usage_key_id}")
        except ClientError as error:
            raise Boto3Exception(service="ses") from error

        return new_usage_key


class UsageKeyServiceContext:
    @property
    @lru_cache(maxsize=None)
    def ssm_config_loader(self) -> SsmConfigLoader:
        parameter_path_prefix = os.environ.get("PARAMETER_PATH_PREFIX")
        return SsmConfigLoader(self.ssm_client, parameter_path_prefix)

    @property
    @lru_cache(maxsize=None)
    def ssm_config(self) -> dict:
        return self.ssm_config_loader.load_config("ssm")

    @property
    @lru_cache(maxsize=None)
    def apigateway_config(self) -> dict:
        return self.ssm_config_loader.load_config("apigateway")

    @property
    @lru_cache(maxsize=None)
    def dynamodb_config(self) -> dict:
        return self.ssm_config_loader.load_config("dynamodb")

    @property
    @lru_cache(maxsize=None)
    def ses_config(self) -> dict:
        return self.ssm_config_loader.load_config("ses")

    @property
    @lru_cache(maxsize=None)
    def ssm_client(self):
        return boto3.client("ssm")

    @property
    @lru_cache(maxsize=None)
    def apigateway_client(self):
        return boto3.client("apigateway")

    @property
    @lru_cache(maxsize=None)
    def dynamodb_client(self):
        return boto3.client("dynamodb")

    @property
    @lru_cache(maxsize=None)
    def ses_client(self):
        return boto3.client("ses")

    @property
    @lru_cache(maxsize=None)
    def api_key_manager(self) -> IApiKeyManager:
        return ApiGatewayKeyManager(
            self.apigateway_client,
            self.apigateway_config["UsagePlanId"]
        )

    @property
    @lru_cache(maxsize=None)
    def usage_key_repository(self) -> IUsageKeyRepository:
        return UsageKeyFromDynamoDB(
            self.dynamodb_client,
            self.dynamodb_config["UsageKeyTableName"]
        )

    @property
    @lru_cache(maxsize=None)
    def automation_manager(self) -> IAutomationManager:
        return SsmAutomationManager(
            self.ssm_client,
            self.ssm_config["AutomationDocumentName"]
        )

    @property
    @lru_cache(maxsize=None)
    def mail_sender(self) -> IMailSender:
        return SesMailSender(
            self.ses_client,
            self.ses_config["FromMailAddress"]
        )

    @property
    @lru_cache(maxsize=None)
    def usage_key_service(self) -> UsageKeyService:
        return UsageKeyService(
            self.api_key_manager,
            self.usage_key_repository,
            self.automation_manager,
            self.mail_sender,
        )
