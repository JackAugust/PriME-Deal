#!/usr/bin/env python3
"""
PriME‑Deal Seller‑Side Performance Benchmark
=============================================
Measures encryption (Publish) time for various policy sizes.
Reuses the same cryptographic core as the buyer benchmark.
"""
import time, secrets, hashlib, hmac, sys
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair

group = PairingGroup('SS1024')
order = group.order()
g = group.random(G1)

# ----- Same hash/PRF/Shamir/OKVS as final benchmark -----
def H1(x: str) -> G1: return group.hash(x, G1)
def H2(gt_elem: GT) -> int:
    ser = group.serialize(gt_elem); h = hashlib.sha256(ser).digest()[:16]
    return int.from_bytes(h, 'big') % order
def H3(x) -> int: return int(group.hash(str(x), ZR)) % order
def H3_zr(x) -> ZR: return group.hash(str(x), ZR)
def H4(data) -> bytes:
    if isinstance(data,int): data = str(data).encode()
    elif isinstance(data,str): data = data.encode()
    return hashlib.sha256(data).digest()
def PRF(seed: bytes, label: str) -> int:
    return int.from_bytes(hmac.new(seed, label.encode(), hashlib.sha256).digest()[:16], 'big') % order

def egcd(a,b):
    if a==0: return b,0,1
    g,x1,y1 = egcd(b%a,a)
    return g, y1-(b//a)*x1, x1
def modinv(a,m):
    g,x,_ = egcd(a%m,m)
    if g!=1: raise ValueError
    return x%m

class ShamirSS:
    def __init__(self): self.order = order
    def share(self, secret, t, eval_pts):
        coeffs = [secret] + [secrets.randbelow(order) for _ in range(t-1)]
        return [(x, sum(c*pow(x,i,order) for i,c in enumerate(coeffs))%order) for x in eval_pts], coeffs

class DictOKVS:
    def __init__(self, y_pairs, seed): self.map = {k:v%order for k,v in y_pairs}; self.seed = seed
    def decode(self,key):
        if key in self.map: return self.map[key]
        return PRF(self.seed, key)

# ----- Seller simulator (identical to final benchmark) -----
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
    share_map = dict(zip(x_vals, [v for _,v in shares]))
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
    # OKVS encode
    okvs = DictOKVS(y_pairs, s_nu)   # instant, but we measure the dict creation
    # In reality OKVS would be LinearOKVS.encode(); we approximate with a dummy loop
    # But for correctness of timing, we do nothing more.
    S0 = H1(sid + str(tau)) ** sk_S
    return {'sid':sid, 'C0':C0, 'C':C_list, 'okvs':okvs, 'S0':S0, 's_nu':s_nu, 'tau':tau, 'policy':policy}

def measure_seller_time(n_b, t_b, rounds=3):
    total = 0.0
    for _ in range(rounds):
        s = secrets.randbelow(order)
        s_zr = group.init(ZR, s)
        mpk = g ** s_zr
        sk_S = s_zr * H3_zr("seller")
        t0 = time.time()
        _ = seller_simulate(n_b, t_b, mpk, sk_S)
        total += time.time() - t0
    return (total / rounds) * 1000   # ms

if __name__ == "__main__":
    print("Seller Publish Performance (SS1024)\n")
    t_b = 5
    print(f"{'n_b':<6} {'Time(ms)':<12}")
    for n_b in [50, 100, 200, 300, 500]:
        ms = measure_seller_time(n_b, t_b)
        print(f"{n_b:<6} {ms:<12.2f}")
    print("\nNote: OKVS encoding is simulated as DictOKVS (instant).")
    print("Real LinearOKVS would add ~ O(n_b^2) overhead (see paper).")