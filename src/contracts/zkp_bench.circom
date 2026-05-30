pragma circom 2.0.0;

// 一个简单的乘加组件：out = (a * b) + c
template MulAdd() {
    signal input a;
    signal input b;
    signal input c;
    signal output out;
    out <== a * b + c;
}

// 主电路：级联 N 个 MulAdd，产生约 3N 个约束
template Cascade(N) {
    signal input in;
    signal output out;

    // 预定义中间信号数组
    signal inter[N + 1];
    inter[0] <== in;

    // 实例化 N 个组件（在初始作用域）
    component ma[N];
    for (var i = 0; i < N; i++) {
        ma[i] = MulAdd();
        ma[i].a <== inter[i];
        ma[i].b <== 2;
        ma[i].c <== i;
        inter[i + 1] <== ma[i].out;
    }
    out <== inter[N];
}

// 目标约束数 ≈ 3 * STAGES
// 15,000 约束 → STAGES = 5000
component main = Cascade(5000);