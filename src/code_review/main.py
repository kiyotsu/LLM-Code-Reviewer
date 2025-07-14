import json
import base64
import logging

from code_review.code_review import CodeReviewService, CodeReviewServiceContext
from common.exception import RequestParameterError
from common.response import ApiResponseBuilder


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

container = CodeReviewServiceContext()


def code_review_handler(event, context):
    """
    コードレビューAPIのハンドラー関数。
    API受信をトリガーにAPI Gatewayを通じて本関数がコールされます。
    Args:
        event (Dict): API Gatewayのリクエスト情報
        context (Dict): Lambdaランタイムコンテキスト
    Returns:
        API Gatewayが期待するレスポンス形式の辞書。
    """
    try:
        # --- リクエストの解析と検証 ---
        body = event.get("body")
        if isinstance(body, str):
            body = json.loads(body)

        # --- ソースコード文字列取得 ---
        source_base64 = body.get("source_base64")
        if not source_base64:
            raise RequestParameterError.not_found("source_base64")

        # --- Base64化を期待 ---
        try:
            source_code = base64.b64decode(source_base64).decode("utf-8")
        except (base64.binascii.Error, UnicodeDecodeError) as error:
            raise RequestParameterError.invalid_format("source_base64", "Base64デコードに失敗") from error

        # --- プログラミング言語取得 ---
        language = body.get("language")
        if not language:
            raise RequestParameterError.not_found("language")

        # --- コードレビューの実行 ---
        code_review_service: CodeReviewService = container.code_review_service
        review_result = code_review_service.excute_review(source_code, language)

        # --- レスポンスの整形 ---
        return ApiResponseBuilder.success(review_result)

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
