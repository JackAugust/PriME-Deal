#!/usr/bin/env python3
"""
PriME‑Deal Extended Scalability & False‑Positive Stress Test
=============================================================
Adds large‑scale n_b and m sweeps, plus deliberate false‑positive injection.
Same cryptographic core as the final benchmark (SS1024, corrected Lagrange).
"""
import time, secrets, random, hashlib, hmac, math, sys
from typing import List, Tuple, Dict

from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair

# ---------- Curve ----------
group = PairingGroup('SS1024')          # symmetric, ~112‑bit security
order = group.order()
g = group.random(G1)

# ---------- Modular inverse (extended gcd) ----------
def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    return g, y1 - (b // a) * x1, x1

def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1: raise ValueError("no inverse")
    return x % m

# ---------- Hash / PRF ----------
def H1(x: str) -> G1:
    return group.hash(x, G1)
def H2(gt_elem: GT) -> int:
    ser = group.serialize(gt_elem)
    h = hashlib.sha256(ser).digest()[:16]
    return int.from_bytes(h, 'big') % order
def H3(x) -> int:
    return int(group.hash(str(x), ZR)) % order
def H3_zr(x) -> ZR:
    return group.hash(str(x), ZR)
def H4(data) -> bytes:
    if isinstance(data, int): data = str(data).encode()
    elif isinstance(data, str): data = data.encode()
    return hashlib.sha256(data).digest()
def PRF(seed: bytes, label: str) -> int:
    return int.from_bytes(hmac.new(seed, label.encode(), hashlib.sha256).digest()[:16], 'big') % order

# ---------- Shamir (CORRECTED) ----------
class ShamirSS:
    def __init__(self):
        self.order = order
    def share(self, secret, t, eval_pts):
        coeffs = [secret] + [secrets.randbelow(order) for _ in range(t-1)]
        shares = []
        for x in eval_pts:
            y = sum(c * pow(x, i, order) for i, c in enumerate(coeffs)) % order
            shares.append((x, y))
        return shares, coeffs
    def reconstruct(self, shares):
        res = 0
        k = len(shares)
        for j in range(k):
            xj, yj = shares[j]
            prod = 1
            for i in range(k):
                if i == j: continue
                xi = shares[i][0]
                diff = (xi - xj) % order
                if diff == 0: raise ValueError
                prod = (prod * xi) % order
                prod = (prod * modinv(diff, order)) % order
            res = (res + yj * prod) % order
        return res

# ---------- DictOKVS ----------
class DictOKVS:
    def __init__(self, y_pairs, seed):
        self.map = {k: v % order for k, v in y_pairs}
        self.seed = seed
    def decode(self, key):
        if key in self.map:
            return self.map[key]
        return PRF(self.seed, key)

# ---------- Bloom Filter ----------
class BloomFilter:
    def __init__(self, capacity, error_rate=0.001):
        self.size = int(-capacity * math.log(error_rate) / (math.log(2)**2))
        self.num_hashes = int(self.size / capacity * math.log(2)) + 1
        self.bits = bytearray((self.size + 7) // 8)
    def _hashes(self, data):
        h = hashlib.sha256(data).digest()
        for i in range(self.num_hashes):
            yield int.from_bytes(h[4*i:4*i+4], 'big') % self.size
    def insert(self, data):
        for idx in self._hashes(data):
            byte, bit = divmod(idx, 8)
            self.bits[byte] |= 1 << bit
    def lookup(self, data):
        return all((self.bits[idx//8] >> (idx%8)) & 1 for idx in self._hashes(data))

# ---------- Seller & Buyer (same as final) ----------
def seller_simulate(n_b, t_b, mpk, sk_S, uid_S="seller"):
    sid = uid_S + "_" + str(int(time.time()*1000))
    tau = secrets.randbelow(order)
    rho = secrets.randbelow(order)
    rho_zr = group.init(ZR, rho)
    C0 = g ** rho_zr
    s_nu = secrets.token_bytes(16)
    s_r = secrets.token_bytes(16)
    policy = [f"attr_{i}" for i in range(n_b)]
    x_vals = [H3(p) for p in policy]
    shamir = ShamirSS()
    (shares, _) = shamir.share(tau, t_b, x_vals)
    share_map = dict(zip(x_vals, [v for _, v in shares]))
    C_list, y_pairs = [], []
    for p in policy:
        x = H3(p)
        s_i = share_map[x]
        r_i = PRF(s_r, p)
        r_zr = group.init(ZR, r_i)
        C_i = g ** r_zr
        K_i = H2(pair(H1(p), mpk) ** r_zr)
        tag_i = H4(K_i)
        nu_i = PRF(s_nu, p)
        y_i = (s_i + nu_i + H3(K_i)) % order
        C_list.append((C_i, tag_i))
        y_pairs.append((p, y_i))
    okvs = DictOKVS(y_pairs, s_nu)
    bf = BloomFilter(capacity=int(n_b*1.5), error_rate=0.001)
    for p in policy:
        bf.insert(group.serialize(group.hash(str(p), ZR)))
    S0 = H1(sid + str(tau)) ** sk_S
    return {'sid':sid, 'C0':C0, 'C':C_list, 'okvs':okvs, 'filter':bf,
            'S0':S0, 's_nu':s_nu, 'tau':tau, 'policy':policy}

def buyer_reconstruct(pp, buyer_attrs, dk_dict, seller_data, t_b, use_filter=True):
    pk_S = pp['pk_S']; S0 = seller_data['S0']; sid = seller_data['sid']
    s_nu = seller_data['s_nu']; okvs = seller_data['okvs']
    C_list = seller_data['C']; bf = seller_data['filter']
    policy_set = set(seller_data['policy'])

    filtered, fp = [], 0
    for a in buyer_attrs:
        if use_filter:
            if bf.lookup(group.serialize(group.hash(str(a), ZR))):
                filtered.append(a)
                if a not in policy_set: fp += 1
        else:
            filtered.append(a)

    pairings = 0
    shares = []
    for a in filtered:
        z = okvs.decode(a)
        nu = PRF(s_nu, a)
        D_a = dk_dict[a]
        for C_i, tag_i in C_list:
            Kp = H2(pair(C_i, D_a))
            pairings += 1
            if H4(Kp) == tag_i:
                u = (z - nu - H3(Kp)) % order
                shares.append((H3(a), u))
                break   # one match per attribute

    if len(shares) < t_b:
        return None, pairings, 0, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

    shamir = ShamirSS()
    try:
        tau_c = shamir.reconstruct(shares[:t_b])
    except ValueError:
        return None, pairings, 1, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

    if pair(S0, g) == pair(H1(sid + str(tau_c)), pk_S):
        return tau_c, pairings, 1, True, {'filtered_cnt':len(filtered), 'false_positives':fp}
    else:
        return None, pairings, 1, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

# ---------- Scenario generator (with configurable fake attributes) ----------
def generate_scenario(n_b, m, t_b, overlap_min=None, fake_count=0):
    """
    fake_count: number of extra attributes NOT in the policy (to trigger FPs).
    """
    if overlap_min is None: overlap_min = t_b
    overlap_min = min(overlap_min, n_b)
    policy = [f"attr_{i}" for i in range(n_b)]
    common = random.sample(policy, overlap_min)
    extra_req = [f"req_{i}" for i in range(m - overlap_min)]
    buyer_attrs = set(common + extra_req)
    # Add fake attributes to deliberately test false positives
    if fake_count > 0:
        fake_attrs = {f"fake_{i}" for i in range(fake_count)}
        buyer_attrs.update(fake_attrs)
    return policy, buyer_attrs

# ---------- Extended experiment runner ----------
ZKP_TIMES = {2:1.8, 3:2.0, 4:2.3, 5:2.5, 10:3.0, 15:4.0, 20:5.0}

def run_single_config(n_b, m, t_b, rounds=3, use_filter=True, fake_count=0):
    total_recon = total_pairings = total_trials = 0.0
    total_filtered = total_fp = 0
    success = 0
    for r in range(rounds):
        s = secrets.randbelow(order)
        s_zr = group.init(ZR, s)
        mpk = g ** s_zr
        sk_S = s_zr * H3_zr("seller")
        pp = {'g':g, 'mpk':mpk, 'pk_S':g ** sk_S}
        seller_data = seller_simulate(n_b, t_b, mpk, sk_S)
        policy, buyer_attrs = generate_scenario(n_b, m, t_b, fake_count=fake_count)
        dk = {a: H1(a) ** s_zr for a in buyer_attrs}
        t_start = time.time()
        tau_prime, pairings, trials, ok, stats = buyer_reconstruct(pp, buyer_attrs, dk, seller_data, t_b, use_filter)
        elapsed = time.time() - t_start
        total_recon += elapsed
        total_pairings += pairings
        total_trials += trials
        total_filtered += stats['filtered_cnt']
        total_fp += stats['false_positives']
        if ok and tau_prime == seller_data['tau']:
            success += 1
    effective_rounds = rounds
    avg_recon = total_recon / effective_rounds
    return {
        'recon_ms': avg_recon * 1000,
        'pairings': total_pairings / effective_rounds,
        'trials': total_trials / effective_rounds,
        'avg_filtered': total_filtered / effective_rounds,
        'avg_fp': total_fp / effective_rounds,
        'success_rate': success / effective_rounds,
        'total_sec': avg_recon + ZKP_TIMES.get(t_b, 3.0),
    }

# ---------- Extended sweeps ----------
def main():
    print("Extended Scalability and FP Stress Test")
    sweeps = []

    # Sweep 1: large policy sizes (filter ON only)
    for n_b in [100, 200, 300, 500]:
        sweeps.append(('large_nb', n_b, 20, 5, 0))

    # Sweep 2: large buyer attribute sets (filter ON, no fake)
    for m in [20, 30, 50]:
        sweeps.append(('large_m', 200, m, 5, 0))

    # Sweep 3: false‑positive injection (fixed n_b=200, m=20, t_b=5)
    for fake in [0, 10, 20, 50]:   # add 10‑50 fake attributes
        sweeps.append(('fp_stress', 200, 20, 5, fake))

    out_file = 'prime_deal_extended_bench.csv'
    with open(out_file, 'w') as f:
        f.write("sweep,n_b,m,t_b,fake,recon_ms,total_sec,pairings,trials,avg_filtered,avg_fp,success_rate\n")
        for sweep_name, n_b, m, t_b, fake in sweeps:
            print(f"\n[Extended] {sweep_name} n_b={n_b} m={m} t_b={t_b} fake={fake}")
            res = run_single_config(n_b, m, t_b, rounds=3, use_filter=True, fake_count=fake)
            line = (f"{sweep_name},{n_b},{m},{t_b},{fake},"
                    f"{res['recon_ms']:.2f},{res['total_sec']:.2f},"
                    f"{res['pairings']:.1f},{res['trials']:.1f},"
                    f"{res['avg_filtered']:.1f},{res['avg_fp']:.1f},"
                    f"{res['success_rate']:.2f}")
            print(f"  => {line.replace(',', '  ')}")
            f.write(line + '\n')
    print(f"\nExtended results saved to {out_file}")

if __name__ == "__main__":
    main()