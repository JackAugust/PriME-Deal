#!/usr/bin/env python3
"""
PriME‑Deal DEBUG – fixed modular inverse for Python 3.6.
"""
import time, secrets, random, hashlib, hmac, math, sys
from typing import List, Tuple, Dict

from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair

group = PairingGroup('SS1024')
order = group.order()
g = group.random(G1)

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

def egcd(a, b):
    if a == 0:
        return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    x = y1 - (b // a) * x1
    y = x1
    return g, x, y

def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1:
        raise ValueError("no inverse")
    return x % m

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

class DictOKVS:
    def __init__(self, y_pairs, seed):
        self.map = {k: v % order for k, v in y_pairs}
        self.seed = seed
    def decode(self, key):
        if key in self.map:
            return self.map[key]
        return PRF(self.seed, key)

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

if __name__ == "__main__":
    n_b, m, t_b = 10, 5, 3
    use_filter = True

    s = secrets.randbelow(order)
    s_zr = group.init(ZR, s)
    mpk = g ** s_zr
    sk_S = s_zr * H3_zr("seller")
    pk_S = g ** sk_S

    sid = "seller_" + str(int(time.time()*1000))
    tau = secrets.randbelow(order)
    rho = secrets.randbelow(order)
    rho_zr = group.init(ZR, rho)
    C0 = g ** rho_zr
    s_nu = secrets.token_bytes(16)
    s_r = secrets.token_bytes(16)
    policy = [f"attr_{i}" for i in range(n_b)]
    x_vals = [H3(p) for p in policy]
    shamir = ShamirSS()
    (shares, coeffs) = shamir.share(tau, t_b, x_vals)
    share_map = dict(zip(x_vals, [v for _, v in shares]))

    print("=== SELLER ===")
    print(f"tau={tau}")
    for p, x, s_i in zip(policy, x_vals, [v for _,v in shares]):
        print(f"  {p}: x={x}, s_i={s_i}")

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

    print("\n=== BUYER ===")
    buyer_attrs = set(policy[:t_b] + [f"req_{i}" for i in range(m - t_b)])
    dk = {a: H1(a) ** s_zr for a in buyer_attrs}
    filtered, fp = [], 0
    for a in buyer_attrs:
        if use_filter:
            if bf.lookup(group.serialize(group.hash(str(a), ZR))):
                filtered.append(a)
                if a not in set(policy): fp += 1
        else:
            filtered.append(a)
    print(f"filtered={filtered}")

    shares_found = []
    for a in filtered:
        z = okvs.decode(a)
        nu = PRF(s_nu, a)
        D_a = dk[a]
        for C_i, tag_i in C_list:
            Kp = H2(pair(C_i, D_a))
            if H4(Kp) == tag_i:
                u = (z - nu - H3(Kp)) % order
                shares_found.append((H3(a), u))
                print(f"  Matched {a}: u={u}, match={u == share_map[H3(a)]}")
                break

    if len(shares_found) < t_b:
        print("INSUFFICIENT SHARES")
        sys.exit(0)

    tau_c = shamir.reconstruct(shares_found[:t_b])
    print(f"\ntau_c={tau_c}\noriginal tau={tau}\nMatch: {tau_c == tau}")

    lhs = pair(S0, g)
    rhs = pair(H1(sid + str(tau_c)), pk_S)
    print(f"Signature match: {lhs == rhs}")