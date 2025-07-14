from botocore.exceptions import ClientError


class ApplicationException(Exception):
    pass


class RequestParameterError(ApplicationException):
    """リクエストパラメータに関するエラーを表す基底例外クラス。"""
    def __init__(self, message: str, parameter_name: str):
        super().__init__(message)
        self.parameter_name = parameter_name

    @classmethod
    def not_found(cls, parameter_name: str) -> "RequestParameterError":
        """必須パラメータが見つからない場合に送出する例外を生成します。"""
        message = f"必須パラメータ '{parameter_name}' が見つかりません。"
        return cls(message, parameter_name)

    @classmethod
    def invalid_format(cls, parameter_name: str, reason: str) -> "RequestParameterError":
        """パラメータのフォーマットが不正な場合に送出する例外を生成します。"""
        message = f"パラメータ '{parameter_name}' のフォーマットが不正です。理由: {reason}"
        return cls(message, parameter_name)


class Boto3Exception(ApplicationException):
    def __init__(self, service: str, reason: str = None):
        super().__init__()
        self._service = service
        self._reason = reason

    @property
    def service(self) -> str:
        return self._service

    @property
    def reason(self) -> str:
        if self._reason:
            return self._reason
        if isinstance(self.__cause__, ClientError):
            return self.__cause__.response.get("Error", {}).get("Code", "UnknownError")
        return "UnknownError"

    @property
    def operation_name(self) -> str:
        if isinstance(self.__cause__, ClientError) and hasattr(self.__cause__, "operation_name"):
            return self.__cause__.operation_name
        return "UnknownOpertaion"

    def __str__(self):
        return f"AWSサービス '{self.service}' のオペレーション '{self.operation_name}' でエラーが発生しました。原因: {self.reason}"
