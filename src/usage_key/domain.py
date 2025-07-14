from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
from typing import Optional, Dict


class KeyStatus(str, Enum):
    PENDING = "PENDING"
    CREATED = "CREATED"


@dataclass(frozen=True)
class User:
    # 利用者名
    name: str

    # 利用者のメールアドレス
    email: str


@dataclass(frozen=True)
class UsageKey:
    # 利用キーID（利用キーを識別するためのユニーク値）
    usage_key_id: str

    # API Gatewayで管理するAPIキーID
    api_key_id: Optional[str]

    # 利用キーユーザー情報
    user: User

    # 利用キーの状態
    status: KeyStatus


class IApiKeyManager(ABC):
    """APIキー管理システムのインターフェース"""
    @abstractmethod
    def create_key(self, name: str) -> Dict[str, str]:
        """キーを作成し、プランに紐付ける。戻り値はキーIDと値を含む辞書。"""
        pass


class IUsageKeyRepository(ABC):
    """利用キーリポジトリのインターフェース"""
    @abstractmethod
    def save_key(self, usage_key: UsageKey):
        """利用キー情報を永続化する"""
        pass

    @abstractmethod
    def get_key(self, usage_key_id: str) -> Optional[UsageKey]:
        """利用キー情報を永続化する"""
        pass

    @abstractmethod
    def delete_key(self, usage_key_id: str):
        """利用キー情報を永続化する"""
        pass



class IAutomationManager(ABC):
    """承認ワークフローなどのオートメーションを実行するシステムのインターフェース"""
    @abstractmethod
    def start_approval_workflow(self, user: User):
        """利用キー発行の承認ワークフローを開始する"""
        pass


class IMailSender(ABC):
    """承認ワークフローなどのオートメーションを実行するシステムのインターフェース"""
    @abstractmethod
    def send_email(self, to_address: str, subject: str, text: str, html: str, reply_tos=None):
        """利用キー発行の承認ワークフローを開始する"""
        pass