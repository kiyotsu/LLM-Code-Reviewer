import json
from typing import Any, Dict, Optional


class ApiResponseBuilder:
    def __init__(self, status_code: int = 200):
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.body: Optional[Any] = None

    def with_body(self, body: Any) -> "ApiResponseBuilder":
        """レスポンスのボディを設定します。"""
        self.body = body
        return self

    def with_headers(self, headers: Dict[str, str]) -> "ApiResponseBuilder":
        """レスポンスのヘッダーを上書き・追加します。"""
        self.headers.update(headers)
        return self

    def with_content_type(self, content_type: str) -> "ApiResponseBuilder":
        """レスポンスのヘッダーを上書き・追加します。"""
        self.headers["Content-Type"] = content_type
        return self

    def build(self) -> Dict[str, Any]:
        """設定された内容から最終的なレスポンス辞書を構築します。"""
        response_body = ""
        if self.body:
            # Content-TypeがJSONならdumpsする
            if self.headers.get("Content-Type") == "application/json":
                response_body = json.dumps(self.body, ensure_ascii=False)
            else:
                response_body = str(self.body)

        return {
            "statusCode": self.status_code,
            "headers": self.headers,
            "body": response_body,
        }

    @staticmethod
    def success(body: Any, status_code: int = 200) -> Dict[str, Any]:
        """成功レスポンスを生成します。"""
        return ApiResponseBuilder(status_code).with_body(body).build()

    @staticmethod
    def error(message: str, status_code: int) -> Dict[str, Any]:
        """汎用的なエラーレスポンスを生成します。"""
        error_body = {"message": message}
        return ApiResponseBuilder(status_code).with_body(error_body).build()

    @staticmethod
    def bad_request(message: str) -> Dict[str, Any]:
        """400 Bad Requestエラーレスポンスを生成します。"""
        return ApiResponseBuilder.error(message, 400)

    @staticmethod
    def internal_server_error(message: str = "An internal server error occurred.") -> Dict[str, Any]:
        """500 Internal Server Errorレスポンスを生成します。"""
        return ApiResponseBuilder.error(message, 500)
