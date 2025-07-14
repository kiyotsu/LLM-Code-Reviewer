# API仕様書
このドキュメントは、LLM Code Reviewer APIの仕様について記述します。

## 1. 利用キー発行依頼API

### 概要
* コードレビューAPIの利用に必要なAPIキーの発行を管理者に依頼します。
* リクエストが正常に受理されると、管理者に承認依頼のメールが送信されます。
* 管理者の承認後、APIキーが利用可能になります。

### パス
`/usagekey`

### HTTPメソッド
POST

### ヘッダー
| キー | 値 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `Content-Type` | `application/json` | ✔ | リクエストボディの形式 |

### リクエストボディ
| キー | 型 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `username` | string | ✔ | APIキーの発行を申請するユーザーのユーザー名 |
| `email` | string | ✔ | APIキーの発行を申請するユーザーのメールアドレス |

#### リクエスト例
```json
{
  "username": "Tom Hanks",
  "email": "tomtom@example.com"
}
```

### レスポンス

#### ステータスコード
| コード | 説明 |
| :--- | :--- |
| `200 OK` | 成功。リクエストを受け付けました。 |
| `400 Bad Request` | リクエストボディが不正です（例：emailが指定されていない）。 |
| `500 Internal Server Error` | サーバー内部でエラーが発生しました。 |

#### レスポンスボディ
成功時は、JSON形式のデータを返します。
```json
{
  "status": "PENDING"
}
```

**statusパラメータの値:**
| status | 説明 |
| :--- | :--- |
| `PENDING` | 発行承認待ちです。 |
| `CREATED` | すでに利用キーが発行されています。<br>管理者に問い合わせてください。 |


## 2. コードレビューAPI

### 概要
指定されたソースコードを、定義済みのコーディングルールに基づきレビューします。

### パス
`/codereview`

### HTTPメソッド
POST

### ヘッダー
| キー | 値 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `Content-Type` | `application/json` | ✔ | リクエストボディの形式 |
| `x-api-key` | `string` | ✔ | 認証用のAPIキー |


### リクエストボディ
| キー | 型 | 必須 | 説明 |
| :--- | :--- | :--- | :--- |
| `source_base64` | string | ✔ | レビュー対象のソースコード（Base64エンコード済み） |
| `language` | string | ✔ | ソースコードのプログラミング言語（例: "Python", "TypeScript"） |

#### リクエスト例
```json
{
  "source_base64": "Ly8gVGhpcyBpcyBhIHRlc3Qgc2NyaXB0...",
  "language": "TypeScript"
}
```

### レスポンス

#### ステータスコード
| コード | 説明 |
| :--- | :--- |
| `200 OK` | 成功。レビュー結果を返却します。 |
| `400 Bad Request` | リクエストボディが不正です（例：`source_base64`が空）。 |
| `403 Forbidden` | 提供されたAPIキーが無効です。 |
| `429 Too Many Requests` | APIの利用回数制限を超えました。 |
| `500 Internal Server Error` | サーバー内部でエラーが発生しました。 |

---

#### レスポンスボディ
成功時は、JSON形式のデータを返します。
```json
{
  "review_result": "NG",
  "review_points": [
    {
      "location": "incNumber",
      "codeline": 2,
      "category": "Readability",
      "overview": "関数名が「incNumber」では、機能が明確ではない",
      "details": "関数名 incNumber() では、この関数が何を行うのかが明確ではありません。関数名は、その機能を端的に表すべきです。",
      "suggestion": "関数名を「divideNumbers」などに変更し、この関数が2つの数値を割る処理を行うことを明確にしましょう。\n\nfunction divideNumbers(a: number, b: number): number {\n  return a / b;\n}"
    }
  ]
}
```

**レスポンスデータ:**
| キー | 型 | 説明 |
| :--- | :--- | :--- |
| `review_result` | string | レビュー結果 (`OK`: 指摘なし, `NG`: 指摘あり) |
| `review_points` | array | 指摘内容の配列。`review_result`が`NG`の場合にのみ含まれます。 |


**review_points オブジェクトの詳細:**

| キー | 型 | 説明 |
| :--- | :--- | :--- |
| `location` | string | 指摘箇所（関数名、変数名など） |
| `codeline` | integer | コード行数 |
| `category` | string | 指摘のカテゴリ（`rules.json`の`category`と一致） |
| `overview` | string | 指摘概要 |
| `details` | string | 指摘詳細 |
| `suggestion` | string | 改善の提案（コード例を含む） |
