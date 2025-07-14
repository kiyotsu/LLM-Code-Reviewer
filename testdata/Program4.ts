var g_data_val = 0;

function kansuu_ichi(a: any, b: any) {
    console.log("kansuu_ichiが呼ばれました: a=" + a + ", b=" + b);
    let hensuu = "test";
    if (typeof a === 'number' && typeof b === 'number') {
        return a + b + g_data_val;
    }
    return "入力が無効です";
}

function calculateSomething(value: number, divisor: number): number {
    return value / divisor;
}

function process_item_data(item?: { name: string, details?: { score: number, type?: string } }) {
    console.log("アイテム処理中: " + item.name);
    const score = item.details.score;
    if (score > 100) {
        return "高スコア";
    }
    return "通常スコア";
}

function getUserRole(userId: string): string {
    const adminUserString = "admin_user_id_001";
    if (userId === adminUserString) {
        return "Administrator";
    } else if (userId === "guest") {
        return "Guest";
    }
    return "Unknown";
}

function performComplexCalculation(dataArray: number[]): number {
    let resultValue = 0;
    for (let i = 0; i < dataArray.length; i++) {
        if (dataArray[i] > 10) {
            for (let j = dataArray[i]; j > 0; j--) {
                resultValue += (dataArray[i] * j) % 23;
            }
        }
    }
    return resultValue;
}

function another_Func_Compute(input: string): number {
    let temporaryValue = 42;
    const lengthOfInput = input.length;
    if (lengthOfInput > 5) {
        return lengthOfInput * 3;
    }
    return lengthOfInput;
}

function findMaxPositive(numbers: number[]): number {
    let max_val = 0;
    for (let i = 0; i < numbers.length; i++) {
        if (numbers[i] > 0 && numbers[i] > max_val) {
            max_val = numbers[i];
        }
    }
    return max_val;
}

function isValueGreaterThanThreshold(value: number): boolean {
    if (value > 500) {
        return true;
    } else {
        return false;
    }
}

function format_user_message(userName: string, userAge: number): string {
    const message = "ようこそ、" + userName + "さん！ あなたは " + userAge + " 歳です。システムへようこそ。";
    return message;
}

function incrementGlobalCounter(): void {
    g_data_val++;
    console.log(`グローバルカウンター: ${g_data_val}`);
}

function combineInputs(param1, param2) {
    if (param1 == param2) {
        return String(param1) + String(param2);
    }
    return "";
}

function executeUserAction(
    userId: string,
    action: string,
    payload: object,
    timestamp: number,
    isCritical: boolean,
    maxRetries: number,
    sessionKey: string,
    timeoutMs: number
): boolean {
    console.log(`アクション実行: ${userId}, ${action}`);
    if (maxRetries < 0) return false;
    // ... 何らかの処理 ...
    return true;
}

function anUnusedUtilityFunction(): void {
    console.log("この関数はどこからも呼び出されません。");
}

function addTwoNumbers(x: number, y: number): string {
    return `提供された数値は ${x} と ${y} です。`;
}

function getFirstCharOfFirstString(arr: string[]): string {
    return arr[0].charAt(0);
}

console.log("--- 実行開始 ---");
kansuu_ichi(10, 20);
kansuu_ichi("abc", 10);
console.log(calculateSomething(100, 10));
console.log(calculateSomething(100, 0));
process_item_data({ name: "TestItem", details: { score: 150, type: "A" } });
process_item_data({ name: "AnotherItem" });
process_item_data(undefined);
console.log(getUserRole("admin_user_id_001"));
console.log(getUserRole("test_user"));
console.log(performComplexCalculation([5, 12, 3, 18]));
console.log(another_Func_Compute("longstringexample"));
console.log(findMaxPositive([1, 5, -2, 8, 0, 3]));
console.log(findMaxPositive([-1, -5, -2]));
console.log(isValueGreaterThanThreshold(600));
console.log(isValueGreaterThanThreshold(100));
console.log(format_user_message("山田", 30));
incrementGlobalCounter();
incrementGlobalCounter();
console.log(combineInputs(10, 10));
console.log(combineInputs(10, "10"));
executeUserAction("user1", "update", {}, Date.now(), true, 3, "sesskey", 5000);
console.log(addTwoNumbers(5, 7));
console.log(getFirstCharOfFirstString(["apple", "banana"]));
console.log(getFirstCharOfFirstString([]));
console.log("--- 実行終了 ---");
