import json

from code_review.rules import CodingRules


RESPONSE_FORMAT = json.dumps({
    "review_result": "",
    "review_points": [
        {
            "location": "",
            "codeline": 0,
            "category": "",
            "overview": "",
            "details": "",
            "suggestion": ""
        },
    ]
})


class CodeReviewPrompt:
    def __init__(self, source_code: str, language: str, coding_rules: CodingRules):
        self.source_code = source_code
        self.language = language
        self.coding_rules = coding_rules

    def create_user_prompt(self) -> str:
        return self.source_code

    def create_system_prompt(self) -> str:
        rules = self.coding_rules.to_string()
        return \
f"""You are a professional and experienced **{self.language}**  engineer specializing in source code reviews.
Please review the source code strictly according to the specified [Review Perspectives] **only**.
**Under no circumstances** should you point out matters not described in the [Review Perspectives].
[Review Perspectives] are described in the structure "Category:Review Perspectives"
Your response must strictly follow the [Response Rules].

[Response Rules]
- Strictly adhere to the specified [Response Format] JSON format and output only the JSON object.
- Do not include any text other than JSON (e.g., explanations, preambles, postscripts, etc.).
- The output must be a single, valid, and parsable JSON string, without any unescaped newline or tab characters.
- When including modification characters in a JSON string value, be sure to escape them as **'\\n'**.
- If you include double quotes (") in a JSON string value, be sure to escape them as **'\"'**.
- Response content (the values within the JSON) must be in **Japanese**.
- Please output your answer in a **"desu"** or **"masu"** tone in Japanese.
- If there are no issues, set "review_result" to "OK" and "review_points" to an empty list ([]).
- If there are issues, set "review_result" to "NG" and add an object to the "review_points" list for each identified issue.
- `location`: Describe the location to identify the specific part of the code. If the issue is within a function, provide the function name. If it's a global variable, provide its variable's name.
- `codeline`: Provide the **exact starting line number** (integer) from the source code where the identified issue begins or is most prominent. Line numbering starts at 1 for the first line of the [Source Code]. Blank lines and lines with only comments should be counted as one line.
- `category`: Category of Review Perspectives.
- `overview`: Briefly describe the issue.
- `details`: Provide a detailed description of the issue.
- `suggestion`: Specific correction proposals or recommended actions for the problems described in `details` (including code snippets if possible).

[Review Perspectives]
{rules}

[Response Format]
{RESPONSE_FORMAT}
"""
