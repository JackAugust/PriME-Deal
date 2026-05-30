#!/usr/bin/env python3
"""
PriME‑Deal Complete Performance Evaluation on BN254
====================================================
Covers:
  - Micro‑benchmarks (pairing, exponentiation, hash)
  - Seller Publish time (varying n_b)
  - Buyer Reconstruction (small & large scale, false‑positive stress)
Curve: BN254 (Type‑3 asymmetric, 128‑bit security)
"""
import time, secrets, random, hashlib, hmac, math, sys
from typing import List, Tuple, Dict

from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair

# ===================== Curve =====================
group = PairingGroup('BN254')                # 128‑bit security, Type‑3
order = group.order()
g1 = group.random(G1)                        # generator for G1
g2 = group.random(G2)                        # generator for G2 (only for reference)

# ===================== Modular inverse (extended gcd) =====================
def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    return g, y1 - (b // a) * x1, x1

def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1: raise ValueError("no inverse")
    return x % m

# ===================== Hash & PRF (adapted to BN254) =====================
def H1(x: str) -> G2:
    """Hash to G2 (required for asymmetric pairings)"""
    return group.hash(x, G2)

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

# ===================== Shamir Secret Sharing =====================
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

# ===================== DictOKVS (simulates linear OKVS) =====================
class DictOKVS:
    def __init__(self, y_pairs, seed):
        self.map = {k: v % order for k, v in y_pairs}
        self.seed = seed
    def decode(self, key):
        if key in self.map:
            return self.map[key]
        return PRF(self.seed, key)

# ===================== Bloom Filter =====================
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

# ===================== Seller Simulator (BN254 adaptation) =====================
def seller_simulate(n_b, t_b, mpk, sk_S, uid_S="seller", bf_error_rate=0.001):
    sid = uid_S + "_" + str(int(time.time()*1000))
    tau = secrets.randbelow(order)
    rho = secrets.randbelow(order)
    rho_zr = group.init(ZR, rho)
    C0 = g1 ** rho_zr                         # G1 element
    s_nu = secrets.token_bytes(16)
    s_r = secrets.token_bytes(16)
    policy = [f"attr_{i}" for i in range(n_b)]
    x_vals = [H3(p) for p in policy]
    shamir = ShamirSS()
    (shares, _) = shamir.share(tau, t_b, x_vals)
    share_map = dict(zip(x_vals, [v for _, v in shares]))
    C_list = []
    y_pairs = []
    for p in policy:
        x = H3(p)
        s_i = share_map[x]
        r_i = PRF(s_r, p)
        r_zr = group.init(ZR, r_i)
        C_i = g1 ** r_zr                        # G1
        # mpk is in G1, H1(p) is in G2 -> pair(G2, G1) is valid
        K_i = H2(pair(H1(p), mpk) ** r_zr)
        tag_i = H4(K_i)
        nu_i = PRF(s_nu, p)
        y_i = (s_i + nu_i + H3(K_i)) % order
        C_list.append((C_i, tag_i))
        y_pairs.append((p, y_i))
    okvs = DictOKVS(y_pairs, s_nu)
    bf = BloomFilter(capacity=int(n_b*1.5), error_rate=bf_error_rate)
    for p in policy:
        bf.insert(group.serialize(group.hash(str(p), ZR)))
    S0 = H1(sid + str(tau)) ** sk_S           # H1 -> G2, sk_S ZR -> G2
    return {'sid':sid, 'C0':C0, 'C':C_list, 'okvs':okvs, 'filter':bf,
            'S0':S0, 's_nu':s_nu, 'tau':tau, 'policy':policy}

# ===================== Buyer Reconstruction (BN254) =====================
def buyer_reconstruct(pp, buyer_attrs, dk_dict, seller_data, t_b, use_filter=True):
    pk_S = pp['pk_S']          # G1
    S0 = seller_data['S0']     # G2
    sid = seller_data['sid']
    s_nu = seller_data['s_nu']
    okvs = seller_data['okvs']
    C_list = seller_data['C']
    bf = seller_data['filter']
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
        D_a = dk_dict[a]          # H1(a)^s, G2 element
        for C_i, tag_i in C_list:
            # pair(G1, G2) = pair(G2, G1) in Charm, we use pair(C_i, D_a) where C_i ∈ G1, D_a ∈ G2
            Kp = H2(pair(C_i, D_a))
            pairings += 1
            if H4(Kp) == tag_i:
                u = (z - nu - H3(Kp)) % order
                shares.append((H3(a), u))
                break

    if len(shares) < t_b:
        return None, pairings, 0, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

    shamir = ShamirSS()
    try:
        tau_c = shamir.reconstruct(shares[:t_b])
    except ValueError:
        return None, pairings, 1, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

    # Verify e(S0, g1) = e(H1(sid||tau_c), pk_S)   S0 ∈ G2, g1 ∈ G1
    lhs = pair(S0, g1)
    rhs = pair(H1(sid + str(tau_c)), pk_S)         # H1 ∈ G2, pk_S ∈ G1
    if lhs == rhs:
        return tau_c, pairings, 1, True, {'filtered_cnt':len(filtered), 'false_positives':fp}
    else:
        return None, pairings, 1, False, {'filtered_cnt':len(filtered), 'false_positives':fp}

# ===================== Micro‑benchmarks =====================
def micro_benchmarks():
    print("=== Micro‑benchmarks on BN254 ===")
    g1_ = g1
    g2_ = group.random(G2)
    zr = group.random(ZR)
    # Pairing
    start = time.time()
    for _ in range(20): pair(g1_, g2_)
    t = (time.time() - start) / 20 * 1000
    print(f"pair (G1,G2) : {t:.3f} ms")

    # Exp G1
    start = time.time()
    for _ in range(20): g1_ ** zr
    t = (time.time() - start) / 20 * 1000
    print(f"G1 ** ZR    : {t:.3f} ms")

    # Exp G2
    start = time.time()
    for _ in range(20): g2_ ** zr
    t = (time.time() - start) / 20 * 1000
    print(f"G2 ** ZR    : {t:.3f} ms")

    # Hash to G2
    start = time.time()
    for _ in range(20): H1("test")
    t = (time.time() - start) / 20 * 1000
    print(f"H1 to G2    : {t:.3f} ms")

    # Hash to ZR
    start = time.time()
    for _ in range(20): H3("test")
    t = (time.time() - start) / 20 * 1000
    print(f"H3 to ZR    : {t:.6f} ms\n")

# ===================== Seller Benchmark =====================
def seller_benchmark():
    print("=== Seller Publish Time (BN254) ===")
    t_b = 5
    results = []
    for n_b in [10, 20, 30, 40, 400]:
    # for n_b in [50, 100, 200, 300, 500]:
        s = secrets.randbelow(order)
        s_zr = group.init(ZR, s)
        mpk = g1 ** s_zr
        sk_S = s_zr * H3_zr("seller")
        start = time.time()
        _ = seller_simulate(n_b, t_b, mpk, sk_S)
        elapsed = (time.time() - start) * 1000
        results.append((n_b, elapsed))
        print(f"n_b={n_b:3d}  {elapsed:.2f} ms")
    print()
    return results

# ===================== Buyer Benchmark (small + large + fp) =====================
def run_buyer_config(n_b, m, t_b, rounds=3, use_filter=True, fake_count=0, bloom_error_rate=0.001):
    total_recon = total_pairings = total_trials = 0.0
    total_filtered = total_fp = 0
    success = 0
    for r in range(rounds):
        s = secrets.randbelow(order)
        s_zr = group.init(ZR, s)
        mpk = g1 ** s_zr
        sk_S = s_zr * H3_zr("seller")
        pp = {'pk_S': g1 ** sk_S}
        seller_data = seller_simulate(n_b, t_b, mpk, sk_S, bf_error_rate=bloom_error_rate)

        # generate buyer attrs with optional fake entries
        overlap = min(t_b, n_b)
        policy = seller_data['policy']
        common = random.sample(policy, overlap)
        extra_req = [f"req_{i}" for i in range(m - overlap)]
        buyer_attrs = set(common + extra_req)
        if fake_count > 0:
            fake_attrs = {f"fake_{i}" for i in range(fake_count)}
            buyer_attrs.update(fake_attrs)

        dk = {a: H1(a) ** s_zr for a in buyer_attrs}
        t0 = time.time()
        tau_prime, pairings, trials, ok, stats = buyer_reconstruct(pp, buyer_attrs, dk, seller_data, t_b, use_filter)
        elapsed = time.time() - t0
        total_recon += elapsed
        total_pairings += pairings
        total_trials += trials
        total_filtered += stats['filtered_cnt']
        total_fp += stats['false_positives']
        if ok and tau_prime == seller_data['tau']:
            success += 1
    N = rounds
    return {
        'recon_ms': (total_recon / N) * 1000,
        'pairings': total_pairings / N,
        'trials': total_trials / N,
        'avg_filtered': total_filtered / N,
        'avg_fp': total_fp / N,
        'success_rate': success / N,
    }

def buyer_benchmark():
    print("=== Buyer Reconstruction Performance (BN254) ===")

    # small‑scale sweeps (reuse previous params)
    sweeps_small = [
        ('policy_sm', [(n_b, 5, 3) for n_b in [40]]),
        ('attrs_sm', [(10, m, 3) for m in [3,4,5,6,7,8,9,10]]),
        ('attrs_sm', [(20, m, 3) for m in [3,4,5,6,7,8,9,10]]),
        ('attrs_sm', [(30, m, 3) for m in [3,4,5,6,7,8,9,10]]),
        ('attrs_sm', [(40, m, 3) for m in [3,4,5,6,7,8,9,10]]),
        ('attrs_sm', [(50, m, 3) for m in [3,4,5,6,7,8,9,10]]),
        ('threshold_sm', [(10, 5, t_b) for t_b in [2,3,4,5]]),
        ('threshold_sm', [(20, 5, t_b) for t_b in [2,3,4,5]]),
        ('threshold_sm', [(100, 10, t_b) for t_b in [2,3,4,5,6,7,8,9,10]]),
        ('threshold_sm', [(200, 10, t_b) for t_b in [2,3,4,5,6,7,8,9,10]]),
        ('threshold_sm', [(200, 20, t_b) for t_b in [2,3,4,5,6,7,8,9,10]])
    ]
    for sweep, configs in sweeps_small:
        for n_b, m, t_b in configs:
            for use_f in [True, False]:
                res = run_buyer_config(n_b, m, t_b, rounds=3, use_filter=use_f)
                print(f"{sweep} n_b={n_b:2d} m={m:2d} t_b={t_b} filter={'Y' if use_f else 'N'} "
                      f"recon={res['recon_ms']:.2f}ms pair={res['pairings']:.1f} "
                      f"succ={res['success_rate']:.2f} fp={res['avg_fp']:.1f}")

    # large‑scale sweeps (filter ON only)
    print("\n--- Large scale ---")
    for n_b in [400]:
        res = run_buyer_config(n_b, 20, 5, rounds=2, use_filter=True)
        print(f"large_nb n_b={n_b:3d} recon={res['recon_ms']:.2f}ms pair={res['pairings']:.1f}")
    print("\n--- Large scale ---")
    for n_b in [500]:
        res = run_buyer_config(n_b, 50, 5, rounds=2, use_filter=True)
        print(f"large_nb n_b={n_b:3d} recon={res['recon_ms']:.2f}ms pair={res['pairings']:.1f}")

    for m in [10,40]:
        res = run_buyer_config(200, m, 5, rounds=2, use_filter=True)
        print(f"large_m m={m:2d} recon={res['recon_ms']:.2f}ms pair={res['pairings']:.1f}")

    # false‑positive stress
    print("\n--- False‑positive stress ---")
    for fake in [0,10,20,30,40,50]:
        res = run_buyer_config(200, 20, 5, rounds=2, use_filter=True, fake_count=fake)
        print(f"fp_stress fake={fake:2d} recon={res['recon_ms']:.2f}ms pair={res['pairings']:.1f} fp={res['avg_fp']:.1f}")

def false_positive_experiment():
    print("\n=== False Positive Rate Experiment (10 runs, mean ± std) ===")
    error_rates = [0.05, 0.04, 0.03, 0.02, 0.01, 0.005, 0.004, 0.003, 0.002, 0.001]

    configs = [
        ("small",  50,  5, 3, 200),
        ("medium", 200, 20, 5, 200),
        ("large",  500, 50, 5, 200),
    ]

    for label, n_b, m, t_b, fake_count in configs:
        print(f"\n--- Config: {label}, n_b={n_b}, m={m}, t_b={t_b}, fake_count={fake_count} ---")
        for err in error_rates:
            recon_list = []
            pair_list = []
            fp_list = []
            success_count = 0
            for _ in range(10):          # 独立运行 10 次
                res = run_buyer_config(n_b, m, t_b, rounds=1, use_filter=True,
                                       fake_count=fake_count, bloom_error_rate=err)
                recon_list.append(res['recon_ms'])
                pair_list.append(res['pairings'])
                fp_list.append(res['avg_fp'])       # rounds=1 时就是单次假阳性数
                if res['success_rate'] == 1.0:
                    success_count += 1

            # 计算均值与标准差（若需要样本标准差可换成 np.std，这里手动实现）
            def mean_std(vals):
                n = len(vals)
                avg = sum(vals) / n
                var = sum((x - avg) ** 2 for x in vals) / (n - 1) if n > 1 else 0.0
                std = var ** 0.5
                return avg, std

            avg_r, std_r = mean_std(recon_list)
            avg_p, std_p = mean_std(pair_list)
            avg_f, std_f = mean_std(fp_list)

            print(f"err={err:.3f}  recon={avg_r:.1f}±{std_r:.1f}ms  "
                  f"pair={avg_p:.1f}±{std_p:.1f}  "
                  f"fp={avg_f:.1f}±{std_f:.1f}  "
                  f"succ={success_count}/10")

# ===================== Main =====================
if __name__ == "__main__":
    print("PriME‑Deal Full Performance Evaluation on BN254\n")
    # micro_benchmarks()
    # seller_benchmark()
    # buyer_benchmark()
    false_positive_experiment() 