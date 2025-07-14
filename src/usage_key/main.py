import json
import logging

from usage_key.domain import User
from usage_key.usage_key import UsageKeyServiceContext
from common.exception import RequestParameterError
from common.response import ApiResponseBuilder


# --- ロガー初期化 ---
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# --- 利用キーサービス関連の初期化 ---
usageKeyServiceContext = UsageKeyServiceContext()


def issutance_request_handler(event, context):
    """
    利用キー発行リクエストのハンドラー関数。
    API受信をトリガーにAPI Gatewayを通じて本関数がコールされます。
    Args:
        event (Dict): API Gatewayのリクエスト情報
        context (Dict): Lambdaランタイムコンテキスト
    Returns:
        API Gatewayが期待するレスポンス形式の辞書。
    """
    try:
        # --- リクエストの解析と検証 ---
        body = event["body"]
        if isinstance(body, str):
            body = json.loads(event["body"])

        # --- 利用者名取得 ---
        username = body.get("username")
        if not username:
            raise RequestParameterError.not_found("username")

        # --- 利用者のメールアドレス取得 ---
        email = body.get("email")
        if not email:
            raise RequestParameterError.not_found("email")

        # --- リクエスト情報からユーザーオブジェクト生成 ---
        user: User = User(username, email)

        # --- 利用キーの発行リクエストを開始 ---
        usage_key_service = usageKeyServiceContext.usage_key_service
        usage_key = usage_key_service.request_issuance(user)

        # --- レスポンスの整形 ---
        return ApiResponseBuilder.success({"status": usage_key.status})

    except RequestParameterError as error:
        # --- リクエスト異常系 ---
        request_id = context.aws_request_id if context else "Unknown"
        logger.exception(f"不正なリクエストです RequestId:{request_id} Parameter: {error.parameter_name}")
        return ApiResponseBuilder.bad_request(f"Invalid '{error.parameter_name}' parameter")

    except Exception:
        # --- 未知のエラー ---
        request_id = context.aws_request_id if context else "Unknown"
        logger.exception(f"予期せぬエラーが発生しました RequestId:{request_id} ")
        return ApiResponseBuilder.internal_server_error("An internal server error occurred")


def create_usage_key_handler(event, context):
    """
    利用キー作成のハンドラー関数。
    オートメーションのフロー中に本関数がコールされます。
    Args:
        event (Dict): オートメーションから渡されるパラメータ情報
        context (Dict): Lambdaランタイムコンテキスト
    Returns:
        なし
    """
    try:
        # --- リクエストの解析と検証 ---
        usage_key_id = event.get("UsageKeyId")
        if not usage_key_id:
            raise RequestParameterError.not_found("UsageKeyId")

        # --- 利用キーの作成 ---
        usage_key_service = usageKeyServiceContext.usage_key_service
        usage_key_service.create_new_usage_key(usage_key_id)

        return {"StatusCode": 200}

    except RequestParameterError as error:
        # --- リクエスト異常系 ---
        request_id = context.aws_request_id if context else "Unknown"
        logger.exception(f"不正なリクエストです RequestId:{request_id} Parameter: {error.parameter_name}")
        return {"StatusCode": 400}

    except Exception:
        # --- 未知のエラー ---
        request_id = context.aws_request_id if context else "Unknown"
        logger.exception(f"予期せぬエラーが発生しました RequestId:{request_id} ")
        return {"StatusCode": 500}
