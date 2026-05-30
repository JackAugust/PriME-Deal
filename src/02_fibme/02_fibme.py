#!/usr/bin/env python3
"""
Fuzzy IB‑ME Extended Benchmark on SS512 (aligned with PriME‑Deal)
Runs all (n_b, m, t_b) combinations used in PriME‑Deal's evaluation.
Outputs fuzzy_ibme_extended.csv.
"""
import time, itertools, numpy as np
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, GT, pair

group = PairingGroup('SS512')
order = group.order()
FAST_DEC = True          # assume correct W_A is known (like tag match)
ROUNDS = 3               # reduce rounds for large n_b to save time

# ---------- helper functions (same as original) ----------
def element_to_int(elem): return int(elem)
def modinv(a, p): return pow(a, p-2, p)
def lagrange_coeff(i, S, x, order):
    num = den = 1
    for j in S:
        if j != i:
            num = (num * (x - j)) % order
            den = (den * (i - j)) % order
    return (num * modinv(den, order)) % order

class FuzzyIBME:
    def __init__(self, d=5):
        self.group = group
        self.d = d
    def attr_to_int(self, attr): return int(group.hash(attr.encode(), ZR))
    def setup(self, n_max):
        # ... (identical to original) ...
        g = group.random(G1); g2 = group.random(G1); g3 = group.random(G1)
        t = [group.random(G1) for _ in range(n_max+1)]
        l = [group.random(G1) for _ in range(n_max+1)]
        alpha = group.random(ZR); beta = group.random(ZR)
        theta1 = group.random(ZR); theta2 = group.random(ZR)
        theta3 = group.random(ZR); theta4 = group.random(ZR)
        g1 = g ** alpha
        eta1 = g ** theta1; eta2 = g ** theta2
        eta3 = g ** theta3; eta4 = g ** theta4
        Y1 = pair(g1, g2) ** (theta1 * theta2)
        Y2 = pair(g3, g ** beta) ** (theta1 * theta2)
        mpk = {'g':g,'g1':g1,'g2':g2,'g3':g3,'Y1':Y1,'Y2':Y2,
               't':t,'l':l,'eta1':eta1,'eta2':eta2,'eta3':eta3,'eta4':eta4,
               'n':n_max,'d':self.d}
        msk = {'alpha':alpha,'beta':beta,'theta1':theta1,'theta2':theta2,
               'theta3':theta3,'theta4':theta4}
        return mpk, msk
    def eval_T(self, x, mpk):
        n = mpk['n']; p = order; N = list(range(1, n+2))
        res = mpk['g2'] ** (pow(x, n, p))
        for i in N:
            delta = lagrange_coeff(i, N, x, p)
            if delta: res *= mpk['t'][i-1] ** delta
        return res
    def eval_H(self, x, mpk):
        n = mpk['n']; p = order; N = list(range(1, n+2))
        res = mpk['g3'] ** (pow(x, n, p))
        for i in N:
            delta = lagrange_coeff(i, N, x, p)
            if delta: res *= mpk['l'][i-1] ** delta
        return res
    def ekgen(self, mpk, msk, S_A):
        # ... (identical) ...
        beta = msk['beta']; t1 = msk['theta1']; t2 = msk['theta2']; p = order
        coeffs_q = [int(beta)] + [int(group.random(ZR)) for _ in range(self.d-1)]
        ek = {}
        for a in S_A:
            x = self.attr_to_int(a)
            qx = sum(c * pow(x, i, p) for i, c in enumerate(coeffs_q)) % p
            r = int(group.random(ZR))
            E = (mpk['g3'] ** (qx * int(t1) * int(t2))) * (self.eval_H(x, mpk) ** r)
            e = mpk['g'] ** r
            ek[a] = (E, e)
        return ek
    def dkgen(self, mpk, msk, S_B, P_A):
        # ... (identical) ...
        alpha = msk['alpha']; beta = msk['beta']
        t1,t2,t3,t4 = msk['theta1'],msk['theta2'],msk['theta3'],msk['theta4']; p = order
        gamma = group.random(ZR); G_ID = group.random(G1)
        coeffs_f = [int(alpha)] + [int(group.random(ZR)) for _ in range(self.d-1)]
        coeffs_h = [int(gamma)] + [int(group.random(ZR)) for _ in range(self.d-1)]
        coeffs_qp = [int(beta)] + [int(group.random(ZR)) for _ in range(self.d-1)]
        dk = {'S_B':{}, 'P_A':{}, 'G_ID':G_ID, 'gamma':gamma}
        for b in S_B:
            x = self.attr_to_int(b)
            fp = sum(c * pow(x, i, p) for i, c in enumerate(coeffs_f)) % p
            hp = sum(c * pow(x, i, p) for i, c in enumerate(coeffs_h)) % p
            k1 = int(group.random(ZR)); k2 = int(group.random(ZR))
            Tx = self.eval_T(x, mpk)
            dkS = {}
            dkS['i0'] = mpk['g'] ** (k1*int(t1)*int(t2) + k2*int(t3)*int(t4))
            dkS['i1'] = (mpk['g2'] ** (-fp*int(t2))) * (G_ID ** (-hp*int(t2))) * (Tx ** (-k1*int(t2)))
            dkS['i2'] = (mpk['g2'] ** (-fp*int(t1))) * (G_ID ** (-hp*int(t1))) * (Tx ** (-k1*int(t1)))
            dkS['i3'] = Tx ** (-k2*int(t4))
            dkS['i4'] = Tx ** (-k2*int(t3))
            dk['S_B'][b] = dkS
        for a in P_A:
            x = self.attr_to_int(a)
            qp = sum(c * pow(x, i, p) for i, c in enumerate(coeffs_qp)) % p
            hp = sum(c * pow(x, i, p) for i, c in enumerate(coeffs_h)) % p
            r1 = int(group.random(ZR)); r2 = int(group.random(ZR))
            Hx = self.eval_H(x, mpk)
            dkP = {}
            dkP['i0'] = mpk['g'] ** (r1*int(t1)*int(t2) + r2*int(t3)*int(t4))
            dkP['i1'] = (mpk['g2'] ** (-2*qp*int(t2))) * (G_ID ** (hp*int(t2))) * (Hx ** (-r1*int(t2)))
            dkP['i2'] = (mpk['g2'] ** (-2*qp*int(t1))) * (G_ID ** (hp*int(t1))) * (Hx ** (-r1*int(t1)))
            dkP['i3'] = Hx ** (-r2*int(t4))
            dkP['i4'] = Hx ** (-r2*int(t3))
            dk['P_A'][a] = dkP
        return dk
    def encrypt(self, mpk, ek, P_B, M, S_A):
        # ... (identical) ...
        s = group.random(ZR); s1 = group.random(ZR); s2 = group.random(ZR); tau = group.random(ZR)
        s_int,s1_int,s2_int,tau_int = int(s),int(s1),int(s2),int(tau)
        K_s = mpk['Y1'] ** s
        K_l = (mpk['Y2'] ** s) * (pair(mpk['g3'], mpk['g']) ** (-tau_int))
        C0 = M * K_s * K_l
        C1 = mpk['eta1'] ** (s_int - s1_int)
        C2 = mpk['eta2'] ** s1_int
        C3 = mpk['eta3'] ** (s_int - s2_int)
        C4 = mpk['eta4'] ** s2_int
        C1_list = {b: self.eval_T(self.attr_to_int(b), mpk) ** s_int for b in P_B}
        C2_list = {a: self.eval_H(self.attr_to_int(a), mpk) ** s_int for a in S_A}
        coeffs_l = [tau_int] + [int(group.random(ZR)) for _ in range(self.d-1)]
        C3_list, C4_list, C5_list = {}, {}, {}
        for a in S_A:
            E_i, e_i = ek[a]
            xi = int(group.random(ZR))
            C3_list[a] = e_i * (mpk['g'] ** xi)
            C4_list[a] = mpk['g'] ** xi
            x = self.attr_to_int(a)
            lx = sum(c * pow(x, i, order) for i, c in enumerate(coeffs_l)) % order
            h1_val = group.hash(group.serialize(C0)+group.serialize(C1)+group.serialize(C2)+group.serialize(C3)+group.serialize(C4)+
                                group.serialize(C1_list.get(a, group.init(G1,1)))+group.serialize(C2_list[a])+
                                group.serialize(C3_list[a])+group.serialize(C4_list[a]), G1)
            xi_chi = int(group.random(ZR))
            C5_list[a] = (E_i ** s_int) * (mpk['g3'] ** lx) * (self.eval_H(x, mpk) ** (s_int * xi)) * (h1_val ** xi_chi)
        return {'C0':C0,'C1':C1,'C2':C2,'C3':C3,'C4':C4,
                'C1_list':C1_list,'C2_list':C2_list,'C3_list':C3_list,'C4_list':C4_list,'C5_list':C5_list}
    def decrypt(self, mpk, dk, CT, S_B, P_A, W_A_hint=None):
        # ... (FAST_DEC mode) ...
        dk_SB, dk_PA = dk['S_B'], dk['P_A']
        C0,C1,C2,C3,C4 = CT['C0'],CT['C1'],CT['C2'],CT['C3'],CT['C4']
        C1_list,C2_list,C3_list,C4_list,C5_list = CT['C1_list'],CT['C2_list'],CT['C3_list'],CT['C4_list'],CT['C5_list']
        base = group.serialize(C0)+group.serialize(C1)+group.serialize(C2)+group.serialize(C3)+group.serialize(C4)
        fallback = group.init(G1,1)
        cand_B = [b for b in S_B if b in C1_list]
        if len(cand_B) < self.d: return None, 0
        if FAST_DEC and W_A_hint is not None:
            W_A = W_A_hint
            for W_B in itertools.combinations(cand_B, self.d):
                try:
                    K_s_inv = group.init(GT,1)
                    for b in W_B:
                        x = self.attr_to_int(b); dk_b = dk_SB[b]
                        N_set = [self.attr_to_int(bb) for bb in W_B]
                        delta = lagrange_coeff(x, N_set, 0, order)
                        K_s_inv *= ( pair(C1_list[b], dk_b['i0']) *
                                     pair(C1, dk_b['i1']) * pair(C2, dk_b['i2']) *
                                     pair(C3, dk_b['i3']) * pair(C4, dk_b['i4']) ) ** delta
                    K_l_inv = group.init(GT,1)
                    for a in W_A:
                        if a not in C2_list or a not in dk_PA: break
                        x = self.attr_to_int(a); dk_a = dk_PA[a]
                        N_set = [self.attr_to_int(aa) for aa in W_A]
                        delta = lagrange_coeff(x, N_set, 0, order)
                        ct_i = base + group.serialize(C1_list.get(a, fallback)) + group.serialize(C2_list[a]) + \
                               group.serialize(C3_list[a]) + group.serialize(C4_list[a])
                        h1_val = group.hash(ct_i, G1)
                        K_l_inv *= ( pair(C1_list.get(a, fallback), dk_a['i0']) *
                                     pair(C1, dk_a['i1']) * pair(C2, dk_a['i2']) *
                                     pair(h1_val, C4_list[a]) * pair(C3_list[a], C2_list[a]) *
                                     pair(C3, dk_a['i3']) * pair(C4, dk_a['i4']) *
                                     pair(C5_list[a], mpk['g']) ) ** delta
                    return C0 * K_s_inv * K_l_inv, 1
                except: continue
            return None, 0
        else:
            # full enumeration (not used)
            return None, 0

# ---------- Benchmark ----------
def run_config(n_b, m, t_b, rounds=ROUNDS):
    fuzzy = FuzzyIBME(d=t_b)   # create fresh instance for each threshold
    # setup with max_n = max(n_b, 200) to cover all
    max_n = max(n_b, 200)
    mpk, msk = fuzzy.setup(max_n)
    enc_times, dec_times = [], []
    for _ in range(rounds):
        S_A = [f"sa{i}" for i in range(n_b)]
        P_B = [f"pb{i}" for i in range(n_b)]
        S_B = [f"sb{i}" for i in range(m)]
        P_A = [f"pa{i}" for i in range(m)]
        common = [f"com{i}" for i in range(t_b)]
        S_A[:t_b] = common; P_B[:t_b] = common
        S_B[:t_b] = common; P_A[:t_b] = common
        ek = fuzzy.ekgen(mpk, msk, S_A)
        dk = fuzzy.dkgen(mpk, msk, S_B, P_A)
        M = group.random(GT)
        t0 = time.time()
        CT = fuzzy.encrypt(mpk, ek, P_B, M, S_A)
        t1 = time.time()
        fuzzy.decrypt(mpk, dk, CT, S_B, P_A, W_A_hint=P_A[:t_b])
        t2 = time.time()
        enc_times.append((t1-t0)*1000)
        dec_times.append((t2-t1)*1000)
    return np.mean(enc_times), np.mean(dec_times)

def main():
    print("Fuzzy IB‑ME Extended Benchmark (SS512)")
    configs = []
    # small scale sweeps
    configs += [('policy_sm', n_b, 5, 3) for n_b in [10,20,30,40,50]]
    configs += [('attrs_sm', 10, m, 3) for m in [3,4,5,6,7,8,9,10]]
    configs += [('attrs_sm', 20, m, 3) for m in [3,4,5,6,7,8,9,10]]
    configs += [('attrs_sm', 30, m, 3) for m in [3,4,5,6,7,8,9,10]]
    configs += [('attrs_sm', 40, m, 3) for m in [3,4,5,6,7,8,9,10]]
    configs += [('attrs_sm', 50, m, 3) for m in [3,4,5,6,7,8,9,10]]
    configs += [('threshold_sm', 10, 5, t_b) for t_b in [2,3,4,5]]
    configs += [('threshold_sm', 20, 5, t_b) for t_b in [2,3,4,5]]
    configs += [('threshold_sm', 100, 10, t_b) for t_b in [2,3,4,5,6,7,8,9,10]]
    configs += [('threshold_sm', 200, 20, t_b) for t_b in [2,3,4,5,6,7,8,9,10]]
    # large scale sweeps (filter ON, but Fuzzy has no filter; still run)
    configs += [('large_nb', n_b, 20, 5) for n_b in [100,200,300,400,500]]
    configs += [('large_m', 200, m, 5) for m in [10,20,30,40,50]]
    # false‑positive stress not applicable (no filter), but we can still run with fake=0
    configs += [('fp_stress', 200, 20, 5)]  # just an extra point

    with open('fuzzy_ibme_extended.csv', 'w') as f:
        f.write("sweep,n_b,m,t_b,enc_ms,dec_ms\n")
        for sweep, n_b, m, t_b in configs:
            print(f"Running {sweep} n_b={n_b} m={m} t_b={t_b} ...", end='', flush=True)
            enc, dec = run_config(n_b, m, t_b, rounds=2 if n_b>100 else ROUNDS)
            print(f" enc={enc:.2f} ms, dec={dec:.2f} ms")
            f.write(f"{sweep},{n_b},{m},{t_b},{enc:.2f},{dec:.2f}\n")

if __name__ == "__main__":
    main()