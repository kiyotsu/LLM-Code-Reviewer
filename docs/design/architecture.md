# アーキテクチャ概要

## 全体像

LLM Code Reviewerは、AWSのサーバーレスアーキテクチャを基盤として構築されています。API Gatewayでリクエストを受け付け、Lambda関数でビジネスロジックを実行し、DynamoDBでデータを永続化します。LLMとの連携にはAmazon Bedrockを利用します。

<img src="../images/architecture.drawio.png">

## 主要コンポーネント

*   **API Gateway**: クライアントからのリクエストを受け付けるAPIのエンドポイントです。利用キーによる認証と流量制御も担当します。
*   **Lambda**: ビジネスロジックを実行するコアコンポーネントです。「利用キー発行」と「コードレビュー」の2つの主要な機能を提供します。
*   **DynamoDB**: 利用キーの情報を格納するNoSQLデータベースです。
*   **Amazon Bedrock**: 大規模言語モデル(LLM)を呼び出し、コードレビュー結果を生成します。
*   **System Manager (Parameter Store)**: BedrockのモデルIDやAPIキーのUsage Plan IDなど、アプリケーションの設定情報を安全に管理します。
*   **SES (Simple Email Service)**: 利用キーの発行時などに、ユーザーへの通知メールを送信します。
*   **SSM (Systems Manager) Automation**: 利用キー発行時の承認ワークフローを実行します。

## ワークフロー

### 利用キー発行

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Backend as LLM Code Reviewer
    participant Admin as システム管理者

    User->>Backend: 1. 利用キー発行リクエスト (POST /usagekey)
    Backend->>Admin: 2. メールで承認依頼を通知
    Admin->>Backend: 3. 承認
    alt 承認された場合
        Backend->>Backend: 4. APIキーを発行
        Backend-->>User: 5. メールでAPIキーを通知
    end
```

### コードレビュー実施

```mermaid
sequenceDiagram
    participant User as ユーザー
    participant Backend as LLM Code Reviewer
    participant Bedrock as Amazon Bedrock

    User->>Backend: 1. レビューリクエスト (POST /codereview)
    Backend->>Bedrock: 2. プロンプトを送信
    Bedrock-->>Backend: 3. レビュー結果を生成・返却
    Note right of Backend: - 結果をJSONにフォーマット
    Backend-->>User: 4. レビュー結果を返却
```