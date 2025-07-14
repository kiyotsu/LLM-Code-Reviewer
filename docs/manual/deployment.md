# デプロイ
LLM-Code-Reviewerのデプロイ手順について記載する。

## 作業に必要なもの
* **Ubuntu22.04:** ビルド、デプロイ作業で使います。
    - Docker
    - AWS CLI v2: 認証情報が設定済みであること。

*  **AWSアカウント:** 管理者権限が付与されていることが望ましいです。

## 前提条件
[事前手順](./00_事前手順.md)を実施済みであること

## 1. ビルド
```bash
# Dockerイメージをビルド。※アプリケーションは単一のDockerイメージで構成されます
docker build -t llm-code-reviewer .
```

## 2. Dockerイメージのアップロード
```bash
# ECRに認証します（<account_id>と<region>を実際の値に置き換えてください）
aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com

# リポジトリを作成します（存在しない場合）
aws ecr create-repository --repository-name llm-code-reviewer

# イメージにタグを付けてプッシュします
docker tag llm-code-reviewer:latest <account_id>.dkr.ecr.<region>.amazonaws.com/llm-code-reviewer:latest
docker push <account_id>.dkr.ecr.<region>.amazonaws.com/llm-code-reviewer:latest
```

## 3. インフラストラクチャのデプロイ
```bash
# （<account_id>と<region>を実際の値に置き換えてください）
aws cloudformation deploy \
    --stack-name LLM-Code-Reviewer \
    --template-file infra/cloudformation/template.yaml \
    --capabilities CAPABILITY_IAM \
    --parameter-overrides ImageUri=<account_id>.dkr.ecr.ap-northeast-1.amazonaws.com/llm-code-reviewer:latest
    --region <region>
```

### スタックパラメータ
* **ImageUri:** コンテナイメージのURL（例：`123456789012.dkr.ecr.ap-northeast-1.amazonaws.com/llm-code-reviewer:latest`）
* **BedrockModelId** 使用するBedrockモデルのID（デフォルト：`anthropic.claude-3-haiku-20240307-v1:0`）
* **BedrockMaxTokens** Bedrockレスポンスの最大トークン数（デフォルト：`"1000"`）
* **BedrockTemperature** Bedrockモデルのtemperature設定（ランダム性を制御、デフォルト：`"0.5"`）
* **BedrockTopP** Bedrockモデルのtop-p設定（多様性を制御、デフォルト：`"0.9"`）