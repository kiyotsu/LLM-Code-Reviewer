from typing import Dict, Any

from botocore.exceptions import ClientError

from common.exception import Boto3Exception


class SsmConfigLoader:
    """
    SSM Parameter Storeから設定を読み込み、キャッシュする責務を持つクラス。
    """
    _cache: Dict[str, Dict[str, Any]] = {}

    def __init__(self, ssm_client: "SSMClient", parameter_path_prefix: str):
        self.ssm_client = ssm_client
        self.parameter_path_prefix = parameter_path_prefix

    def load_config(self, service_name: str) -> Dict[str, Any]:
        if service_name in self._cache:
            return self._cache[service_name]

        full_path = f"{self.parameter_path_prefix}{service_name}/"

        try:
            paginator = self.ssm_client.get_paginator("get_parameters_by_path")
            # Recursive=True に変更し、階層下のパラメータもすべて取得
            pages = paginator.paginate(Path=full_path, Recursive=True, WithDecryption=True)

            # Collect all parameters from all pages
            all_ssm_parameters = [p for page in pages for p in page["Parameters"]]

            # --- パス形式をディクショナリ形式に変換する
            # (例) /path1/path2/path3 を変換すると以下の通り
            # {
            #   "path1": {
            #     "path2": {
            #       "path3": "value"
            #     }
            #    }
            #  } 
            config = {}
            for param_data in all_ssm_parameters:
                key_parts = param_data['Name'].replace(full_path, '', 1).split('/')
                current_level = config
                for i, part in enumerate(key_parts):
                    if i == len(key_parts) - 1:
                        current_level[part] = param_data["Value"]
                    else:
                        current_level = current_level.setdefault(part, {})

            self._cache[service_name] = config
            return config

        except ClientError as error:
            raise Boto3Exception(service="ssm") from error