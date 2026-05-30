pragma circom 2.0.0;

include "/workspace/Paper/DataSharing/Cloud/Silent-Share/node_modules/circomlib/circuits/comparators.circom";

template BuyerCircuit() {
    signal input sid;
    signal input com_AB;
    signal input h_D;
    signal input s_nu;
    signal input t_b;
    signal input S0_x_re;
    signal input S0_x_im;
    signal input S0_y_re;
    signal input S0_y_im;
    signal input mpk_x;
    signal input mpk_y;
    signal input pk_S_x;
    signal input pk_S_y;
    signal input uid_S;

    signal input AB[50];
    signal input omega_B;
    signal input uid_B;
    signal input tau_prime;
    signal input tau_calc;
    signal input U0_a[5];
    signal input U0_u[5];
    signal input z_a[5];
    signal input nu_a[5];
    signal input D[500];
    signal input cred_x_re;
    signal input cred_x_im;
    signal input cred_y_re;
    signal input cred_y_im;

    signal isEqSums[5];
    component eq_comps[5][50];
    signal eq_outs[5][50];
    for (var i = 0; i < 5; i++) {
        for (var j = 0; j < 50; j++) {
            eq_comps[i][j] = IsEqual();
            eq_comps[i][j].in[0] <== U0_a[i];
            eq_comps[i][j].in[1] <== AB[j];
            eq_outs[i][j] <== eq_comps[i][j].out;
        }
        isEqSums[i] <== eq_outs[i][0] + eq_outs[i][1] + eq_outs[i][2] + eq_outs[i][3] + eq_outs[i][4] + eq_outs[i][5] + eq_outs[i][6] + eq_outs[i][7] + eq_outs[i][8] + eq_outs[i][9] + eq_outs[i][10] + eq_outs[i][11] + eq_outs[i][12] + eq_outs[i][13] + eq_outs[i][14] + eq_outs[i][15] + eq_outs[i][16] + eq_outs[i][17] + eq_outs[i][18] + eq_outs[i][19] + eq_outs[i][20] + eq_outs[i][21] + eq_outs[i][22] + eq_outs[i][23] + eq_outs[i][24] + eq_outs[i][25] + eq_outs[i][26] + eq_outs[i][27] + eq_outs[i][28] + eq_outs[i][29] + eq_outs[i][30] + eq_outs[i][31] + eq_outs[i][32] + eq_outs[i][33] + eq_outs[i][34] + eq_outs[i][35] + eq_outs[i][36] + eq_outs[i][37] + eq_outs[i][38] + eq_outs[i][39] + eq_outs[i][40] + eq_outs[i][41] + eq_outs[i][42] + eq_outs[i][43] + eq_outs[i][44] + eq_outs[i][45] + eq_outs[i][46] + eq_outs[i][47] + eq_outs[i][48] + eq_outs[i][49];
        isEqSums[i] === 1;
        U0_u[i] === z_a[i] - nu_a[i];
    }

    tau_prime === tau_calc;

}

component main { public [ sid, com_AB, h_D, s_nu, t_b, S0_x_re, S0_x_im, S0_y_re, S0_y_im, mpk_x, mpk_y, pk_S_x, pk_S_y, uid_S ] } = BuyerCircuit();
