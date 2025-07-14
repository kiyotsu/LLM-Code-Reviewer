# コーディングルール

LLM Code Reviewerがレビュー時に使用するコーディングルールは、`rules.json` ファイルに定義されています。
このドキュメントでは、ルールの定義方法と編集方法について説明します。

## ルールの目的

このコーディングルールは、静的解析ツールでは検出しにくい、以下のような品質に関わる観点をレビューするために定義されています。

*   **可読性 (Readability)**: 変数名や関数名が処理内容を適切に表しているか。
*   **保守性 (Maintainability)**: コードの重複が避けられ、共通ロジックが再利用可能な形で抽出されているか。
*   **堅牢性 (Robustness/Security)**: 予期せぬ入力に対して適切に処理されるか。

これらのルールは、特にプログラミング初学者がより良いコードを書くための指針となることを目的としています。

## ルールファイル (`rules.json`)

ルールはJSON形式で記述します。
ファイルはデプロイ時にコンテナイメージに含まれ、Lambda関数から読み込まれます。

### フォーマット

ルールファイルは、**カテゴリ**をキーとし、そのカテゴリに属する**ルール定義の配列**を値とするJSONオブジェクトです。

```json
{
    "カテゴリ名1": [
        "ルール1-1",
        "ルール1-2"
    ],
    "カテゴリ名2": [
        "ルール2-1"
    ]
}
```

*   **キー (カテゴリ名)**:
    *   コーディングルールのカテゴリを文字列で指定します。（例: `Readability`, `Maintainability`, `Security`）
    *   このカテゴリ名は、レビュー結果のレスポンスにも含まれます。
*   **値 (ルール定義の配列)**:
    *   そのカテゴリに属する具体的なルールを、文字列の配列として記述します。
    *   ルールはLLMへの指示となるため、**英語**で、かつ**具体的で明確な表現**で記述してください。曖昧な表現はLLMの解釈を不安定にし、意図しないレビュー結果につながる可能性があります。

### デフォルトのルール定義

以下は、プロジェクトにデフォルトで含まれている `rules.json` の内容です。

```json
{
    "Maintainability": [
        "Duplicated code is avoided; common logic is extracted into reusable functions or modules."
    ],
    "Readability": [
        "Function and variable names exclusively use English words.",
        "Function and variable names are clearly descriptive of their role or processing content."
    ],
    "Security": [
        "Functions gracefully handle abnormal or unexpected input values to prevent crashes, undefined behavior, or security vulnerabilities."
    ]
}
```

## ルールの編集・追加

新しいレビュー観点を追加したい場合や、既存のルールを修正したい場合は、`src/handlers/code_review/rules.json` ファイルを直接編集し、アプリケーションを再ビルド・再デプロイしてください。
