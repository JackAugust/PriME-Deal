#!/usr/bin/env python3
"""
根据实验参数动态生成 buyer.circom 文件。
参数：NB（策略大小）、TB（阈值）、M（买方属性数）
"""
def generate_circuit(NB: int, TB: int, M: int, output_path="buyer.circom"):
    code = f"""pragma circom 2.0;

include "circomlib/circuits/poseidon.circom";
include "circomlib/circuits/escalarmul.circom";
include "circomlib/circuits/multipairing.circom";

// ---------- 公开输入 ----------
signal input sid;
signal input com_AB;
signal input h_D;
signal input s_nu;
signal input t_b;
// G2 点 S0 (x,y) 两个域元素
signal input S0_x;
signal input S0_y;
// G1 点 mpk
signal input mpk_x;
signal input mpk_y;
// G1 点 pk_S
signal input pk_S_x;
signal input pk_S_y;
signal input uid_S;

// ---------- 私密见证 ----------
// 买方属性集合（固定长度 M，用 0 补齐）
signal input AB[M];
signal input omega_B;
signal input uid_B;
signal input tau_prime;
// U0 = [(a, u)] 长度 TB
signal input U0_a[TB];
signal input U0_u[TB];
// OKVS 向量 D 长度 NB
signal input D[NB];
// 凭证 cred (G1 点)
signal input cred_x;
signal input cred_y;
// CA 公钥 mpk 已在公开输入中给出

// ========== 1. 承诺一致性 ==========
component poseidon_com = Poseidon(M + 1);
for (var i = 0; i < M; i++) {{
    poseidon_com.inputs[i] <== AB[i];
}}
poseidon_com.inputs[M] <== omega_B;
com_AB === poseidon_com.out;

// ========== 2. 凭证有效性 ==========
// H1(uid_B || AB) -> g2^poseidon(…)
component poseidon_cred = Poseidon(M + 1);
poseidon_cred.inputs[0] <== uid_B;
for (var i = 0; i < M; i++) {{
    poseidon_cred.inputs[i+1] <== AB[i];
}}
signal h_cred <== poseidon_cred.out;

// 验证 e(cred, g1) = e(g2^{h_cred}, mpk)
// 即 e(cred, g1) * e(mpk^{-1}, g2^{h_cred}) = 1
// 转换为：e(cred, g1) * e(mpk, g2^{-h_cred}) = 1   (用 -h_cred 等价)
component pairing_cred = MultiPairing(2, 2);
// 第一对： (cred, g1)   cred∈G1, g1∈G2
pairing_cred.G1Points[0][0] <== cred_x;
pairing_cred.G1Points[0][1] <== cred_y;
// g1 生成元在 G2 的固定坐标（硬编码）
pairing_cred.G2Points[0][0] <== 10857046999023057135944570762232829481370756359578518086990519993285655852781;
pairing_cred.G2Points[0][1] <== 11559732032986387107991004021392285783925812861821192530917403151452391805634;
// 第二对： (mpk, g2^{-h_cred})  即 mpk 正常，g2 标量乘 -h_cred
pairing_cred.G1Points[1][0] <== mpk_x;
pairing_cred.G1Points[1][1] <== mpk_y;
// g2 的 -h_cred 倍
component escalar_neg = EscalarMul(2);   // 2 表示 G2
escalar_neg.point[0] <== 10857046999023057135944570762232829481370756359578518086990519993285655852781;
escalar_neg.point[1] <== 11559732032986387107991004021392285783925812861821192530917403151452391805634;
escalar_neg.scalar <== -h_cred;
pairing_cred.G2Points[1][0] <== escalar_neg.out[0];
pairing_cred.G2Points[1][1] <== escalar_neg.out[1];
// 验证配对乘积为 1（GT 单位元）
pairing_cred.out === 1;

// ========== 3. 卖方公钥绑定 pk_S = mpk^{H3(uid_S)} ==========
component poseidon_uidS = Poseidon(1);
poseidon_uidS.inputs[0] <== uid_S;
signal h_uidS <== poseidon_uidS.out;

component escalar_pkS = EscalarMul(1);   // G1
escalar_pkS.point[0] <== mpk_x;
escalar_pkS.point[1] <== mpk_y;
escalar_pkS.scalar <== h_uidS;
pk_S_x === escalar_pkS.out[0];
pk_S_y === escalar_pkS.out[1];

// ========== 4. OKVS 一致性 h_D = Poseidon(D) ==========
component poseidon_D = Poseidon({NB});
for (var i = 0; i < {NB}; i++) {{
    poseidon_D.inputs[i] <== D[i];
}}
h_D === poseidon_D.out;

// ========== 5. 逐条处理 U0 ==========
signal x_a[TB];
signal z_a[TB];
signal nu_a[TB];

for (var i = 0; i < TB; i++) {{
    // a 必须属于 AB（通过相等检查）
    signal found <-- 0;
    for (var j = 0; j < M; j++) {{
        found += (U0_a[i] - AB[j]) * (1 - (U0_a[i] - AB[j])**{order_p_minus_one}) ; // 简化，实际用 IsEqual
    }}
    // 使用 IsEqual 模板
    component isEqual[M];
    signal isEqSum;
    for (var j = 0; j < M; j++) {{
        isEqual[j] = IsEqual();
        isEqual[j].in[0] <== U0_a[i];
        isEqual[j].in[1] <== AB[j];
        isEqSum += isEqual[j].out;
    }}
    isEqSum === 1;   // 必须恰好在一个位置匹配

    // x_a = Poseidon(a)
    component poseidon_a = Poseidon(1);
    poseidon_a.inputs[0] <== U0_a[i];
    x_a[i] <== poseidon_a.out;

    // z = <row(a), D> = Σ D[k] * a^k
    signal pow_a[{NB}];
    pow_a[0] <== 1;
    for (var k = 1; k < {NB}; k++) {{
        pow_a[k] <== pow_a[k-1] * U0_a[i];
    }}
    z_a[i] <== 0;
    for (var k = 0; k < {NB}; k++) {{
        z_a[i] += D[k] * pow_a[k];
    }}

    // nu = Poseidon(s_nu, a)
    component poseidon_nu = Poseidon(2);
    poseidon_nu.inputs[0] <== s_nu;
    poseidon_nu.inputs[1] <== U0_a[i];
    nu_a[i] <== poseidon_nu.out;

    // u = z - nu  (移除了 H3(K'))
    U0_u[i] === z_a[i] - nu_a[i];
}}

// ========== 6. 拉格朗日插值恢复 tau' ==========
signal lagrange_zero[TB];
for (var i = 0; i < TB; i++) {{
    signal num <== 1;
    signal den <== 1;
    for (var j = 0; j < TB; j++) {{
        if (i != j) {{
            num *= (0 - x_a[j]);
            den *= (x_a[i] - x_a[j]);
        }}
    }}
    lagrange_zero[i] <== num / den;
}}

signal tau_calc <== 0;
for (var i = 0; i < TB; i++) {{
    tau_calc += U0_u[i] * lagrange_zero[i];
}}
tau_prime === tau_calc;

// ========== 7. 令牌有效性 e(S0, g1) = e(H1(sid||tau'), pk_S) ==========
component poseidon_token = Poseidon(2);
poseidon_token.inputs[0] <== sid;
poseidon_token.inputs[1] <== tau_prime;
signal h_token <== poseidon_token.out;

component pairing_token = MultiPairing(2, 2);
// 第一对： (S0, g1)  注意 S0 是 G2 点
pairing_token.G2Points[0][0] <== S0_x;
pairing_token.G2Points[0][1] <== S0_y;
pairing_token.G1Points[0][0] <== 1;   // g1 生成元的 x
pairing_token.G1Points[0][1] <== 2;   // y (硬编码)

// 第二对： (pk_S, g2^{-h_token})
pairing_token.G1Points[1][0] <== pk_S_x;
pairing_token.G1Points[1][1] <== pk_S_y;
component escalar_token = EscalarMul(2);
escalar_token.point[0] <== 10857046999023057135944570762232829481370756359578518086990519993285655852781;
escalar_token.point[1] <== 11559732032986387107991004021392285783925812861821192530917403151452391805634;
escalar_token.scalar <== -h_token;
pairing_token.G2Points[1][0] <== escalar_token.out[0];
pairing_token.G2Points[1][1] <== escalar_token.out[1];

pairing_token.out === 1;
"""
    with open(output_path, "w") as f:
        f.write(code)
    print(f"Circuit written to {output_path}")