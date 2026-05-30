pragma circom 2.0.0;

include "circomlib/circuits/mimcsponge.circom";

// 简单哈希包装器
template MimcHash(n) {
    signal input in[n];
    signal output out;
    component sponge = MiMCSponge(n, 1);
    for (var i = 0; i < n; i++) { sponge.ins[i] <== in[i]; }
    out <== sponge.outs[0];
}

template PriMEDealZKP() {
    // 公共输入
    signal input com_AB;
    signal input h_D;
    signal input s_nu;
    signal input S0;
    signal input C0;
    signal input mpk;
    signal input pk_S;
    signal input uid_S;

    // 秘密见证
    signal input omega_B;
    signal input uid_B;
    signal input sk_uid_B;
    signal input tau_prime;
    signal input A_B[10];
    signal input U0_a[5];
    signal input U0_C[5];
    signal input U0_u[5];
    signal input D[10];
    signal input cred_AB;

    // 1) 承诺一致性
    component commit = MimcHash(11);
    commit.in[0] <== A_B[0]; commit.in[1] <== A_B[1];
    commit.in[2] <== A_B[2]; commit.in[3] <== A_B[3];
    commit.in[4] <== A_B[4]; commit.in[5] <== A_B[5];
    commit.in[6] <== A_B[6]; commit.in[7] <== A_B[7];
    commit.in[8] <== A_B[8]; commit.in[9] <== A_B[9];
    commit.in[10] <== omega_B;
    com_AB === commit.out;

    // 2) 凭证有效性 (消耗约束)
    signal tmp1 <== cred_AB * mpk;
    signal tmp2 <== uid_B * pk_S;
    tmp1 === tmp2;

    // 3) 卖方公钥绑定
    signal pk_S_check <== mpk * uid_S;
    pk_S === pk_S_check;

    // 4) OKVS 一致性
    component okvs_hash = MimcHash(10);
    for (var i = 0; i < 10; i++) { okvs_hash.in[i] <== D[i]; }
    h_D === okvs_hash.out;

    // 5) 份额恢复 (展开 5 份)
    // 份额0
    signal z0 <== U0_a[0]*D[0] + U0_a[0]*D[1] + U0_a[0]*D[2] + U0_a[0]*D[3] + U0_a[0]*D[4] +
                 U0_a[0]*D[5] + U0_a[0]*D[6] + U0_a[0]*D[7] + U0_a[0]*D[8] + U0_a[0]*D[9];
    component prf0 = MimcHash(2); prf0.in[0] <== s_nu; prf0.in[1] <== U0_a[0];
    signal nu0 <== prf0.out;
    component k0 = MimcHash(2); k0.in[0] <== U0_C[0]; k0.in[1] <== sk_uid_B;
    signal Kp0 <== k0.out;
    component h3_0 = MimcHash(1); h3_0.in[0] <== Kp0;
    U0_u[0] === z0 - nu0 - h3_0.out;

    // 份额1
    signal z1 <== U0_a[1]*D[0] + U0_a[1]*D[1] + U0_a[1]*D[2] + U0_a[1]*D[3] + U0_a[1]*D[4] +
                 U0_a[1]*D[5] + U0_a[1]*D[6] + U0_a[1]*D[7] + U0_a[1]*D[8] + U0_a[1]*D[9];
    component prf1 = MimcHash(2); prf1.in[0] <== s_nu; prf1.in[1] <== U0_a[1];
    signal nu1 <== prf1.out;
    component k1 = MimcHash(2); k1.in[0] <== U0_C[1]; k1.in[1] <== sk_uid_B;
    signal Kp1 <== k1.out;
    component h3_1 = MimcHash(1); h3_1.in[0] <== Kp1;
    U0_u[1] === z1 - nu1 - h3_1.out;

    // 份额2
    signal z2 <== U0_a[2]*D[0] + U0_a[2]*D[1] + U0_a[2]*D[2] + U0_a[2]*D[3] + U0_a[2]*D[4] +
                 U0_a[2]*D[5] + U0_a[2]*D[6] + U0_a[2]*D[7] + U0_a[2]*D[8] + U0_a[2]*D[9];
    component prf2 = MimcHash(2); prf2.in[0] <== s_nu; prf2.in[1] <== U0_a[2];
    signal nu2 <== prf2.out;
    component k2 = MimcHash(2); k2.in[0] <== U0_C[2]; k2.in[1] <== sk_uid_B;
    signal Kp2 <== k2.out;
    component h3_2 = MimcHash(1); h3_2.in[0] <== Kp2;
    U0_u[2] === z2 - nu2 - h3_2.out;

    // 份额3
    signal z3 <== U0_a[3]*D[0] + U0_a[3]*D[1] + U0_a[3]*D[2] + U0_a[3]*D[3] + U0_a[3]*D[4] +
                 U0_a[3]*D[5] + U0_a[3]*D[6] + U0_a[3]*D[7] + U0_a[3]*D[8] + U0_a[3]*D[9];
    component prf3 = MimcHash(2); prf3.in[0] <== s_nu; prf3.in[1] <== U0_a[3];
    signal nu3 <== prf3.out;
    component k3 = MimcHash(2); k3.in[0] <== U0_C[3]; k3.in[1] <== sk_uid_B;
    signal Kp3 <== k3.out;
    component h3_3 = MimcHash(1); h3_3.in[0] <== Kp3;
    U0_u[3] === z3 - nu3 - h3_3.out;

    // 份额4
    signal z4 <== U0_a[4]*D[0] + U0_a[4]*D[1] + U0_a[4]*D[2] + U0_a[4]*D[3] + U0_a[4]*D[4] +
                 U0_a[4]*D[5] + U0_a[4]*D[6] + U0_a[4]*D[7] + U0_a[4]*D[8] + U0_a[4]*D[9];
    component prf4 = MimcHash(2); prf4.in[0] <== s_nu; prf4.in[1] <== U0_a[4];
    signal nu4 <== prf4.out;
    component k4 = MimcHash(2); k4.in[0] <== U0_C[4]; k4.in[1] <== sk_uid_B;
    signal Kp4 <== k4.out;
    component h3_4 = MimcHash(1); h3_4.in[0] <== Kp4;
    U0_u[4] === z4 - nu4 - h3_4.out;

    // 6) 拉格朗日插值 (5 个点)
    signal den0 <== (U0_a[0]-U0_a[1])*(U0_a[0]-U0_a[2])*(U0_a[0]-U0_a[3])*(U0_a[0]-U0_a[4]);
    signal num0 <== U0_a[1]*U0_a[2]*U0_a[3]*U0_a[4];
    signal ell0 <== num0 / den0;

    signal den1 <== (U0_a[1]-U0_a[0])*(U0_a[1]-U0_a[2])*(U0_a[1]-U0_a[3])*(U0_a[1]-U0_a[4]);
    signal num1 <== U0_a[0]*U0_a[2]*U0_a[3]*U0_a[4];
    signal ell1 <== num1 / den1;

    signal den2 <== (U0_a[2]-U0_a[0])*(U0_a[2]-U0_a[1])*(U0_a[2]-U0_a[3])*(U0_a[2]-U0_a[4]);
    signal num2 <== U0_a[0]*U0_a[1]*U0_a[3]*U0_a[4];
    signal ell2 <== num2 / den2;

    signal den3 <== (U0_a[3]-U0_a[0])*(U0_a[3]-U0_a[1])*(U0_a[3]-U0_a[2])*(U0_a[3]-U0_a[4]);
    signal num3 <== U0_a[0]*U0_a[1]*U0_a[2]*U0_a[4];
    signal ell3 <== num3 / den3;

    signal den4 <== (U0_a[4]-U0_a[0])*(U0_a[4]-U0_a[1])*(U0_a[4]-U0_a[2])*(U0_a[4]-U0_a[3]);
    signal num4 <== U0_a[0]*U0_a[1]*U0_a[2]*U0_a[3];
    signal ell4 <== num4 / den4;

    signal tau_computed <== U0_u[0]*ell0 + U0_u[1]*ell1 + U0_u[2]*ell2 + U0_u[3]*ell3 + U0_u[4]*ell4;
    tau_prime === tau_computed;

    // 7) 令牌签名验证 (简化)
    signal sig_left <== S0 * pk_S;
    signal sig_right <== uid_S * tau_prime;
    sig_left === sig_right;
}

component main { public [ com_AB, h_D, s_nu, S0, C0, mpk, pk_S, uid_S ] } = PriMEDealZKP();