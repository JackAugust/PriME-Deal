#!/usr/bin/env python3
"""
Original IB‑ME (Bilateral Matchmaking Encryption) Benchmark on SS512
====================================================================
Measures Setup, SKGen, RKGen, Enc, Dec, and atomic operations.
"""
import timeit, pickle, base64, sys
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, pair

group = PairingGroup('SS512', secparam=512)

class IBME:
    def __init__(self):
        self._mask = bytes.fromhex('ed27dbfb02752e0e16bc4502d6c732bc5f1cc92ba19b2d93a4e95c597ca42753e93550b52f82b6c13fb8cc0c2fc64487')

    def setup(self):
        r, s, P = group.random(ZR), group.random(ZR), group.random(G1)
        P0 = r * P
        return (P, P0), (r, s)

    def H(self, X):
        return group.hash(X, G1)

    def H_prime(self, X):
        X = bytes([a ^ b for (a, b) in zip(X.encode(), self._mask)])
        return group.hash(X, G1)

    def skgen(self, sk, S):
        _, s = sk
        return s * self.H_prime(S)

    def rkgen(self, sk, R):
        r, s = sk
        H_R = self.H(R)
        return (r * H_R, s * H_R, H_R)

    def encrypt(self, pk, R, ek_S, M):
        P, P0 = pk
        u, t = group.random(ZR), group.random(ZR)
        T, U = t * P, u * P
        H_R = self.H(R)
        k_R = pair(H_R, u * P0)
        k_S = pair(H_R, T + ek_S)
        enc_k_R = group.serialize(k_R)[2:-1]
        enc_k_S = group.serialize(k_S)[2:-1]
        V = bytes([a ^ b ^ c for (a, b, c) in zip(M, enc_k_R, enc_k_S)])
        return (T, U, V)

    def decrypt(self, pk, dk, S, C):
        dk1, dk2, dk3 = dk
        T, U, V = C
        k_R = pair(dk1, U)
        k_S = pair(dk3, T) * pair(self.H_prime(S), dk2)
        enc_k_R = group.serialize(k_R)[2:-1]
        enc_k_S = group.serialize(k_S)[2:-1]
        return bytes([a ^ b ^ c for (a, b, c) in zip(V, enc_k_R, enc_k_S)])


if __name__ == "__main__":
    me = IBME()
    pk, sk = me.setup()
    R, S = "buyer_attr", "seller_attr"
    dk = me.rkgen(sk, R)
    ek = me.skgen(sk, S)
    msg = b"hello world"

    # warm up
    for _ in range(5):
        me.encrypt(pk, R, ek, msg)

    iters, rep = 10, 50

    def bench(stmt, setup, globals_dict=None):
        timer = timeit.Timer(stmt, setup=setup, globals=globals_dict)
        times = timer.repeat(rep, iters)
        return sum(times) / len(times) / iters * 1000

    t_setup = bench(
        "me.setup()",
        "from __main__ import me",
        globals_dict={'me': me}
    )
    t_skgen = bench(
        "me.skgen(sk, S)",
        "from __main__ import me, sk, S",
        globals_dict={'me': me, 'sk': sk, 'S': S}
    )
    t_rkgen = bench(
        "me.rkgen(sk, R)",
        "from __main__ import me, sk, R",
        globals_dict={'me': me, 'sk': sk, 'R': R}
    )
    t_enc = bench(
        "me.encrypt(pk, R, ek, msg)",
        "from __main__ import me, pk, R, ek, msg",
        globals_dict={'me': me, 'pk': pk, 'R': R, 'ek': ek, 'msg': msg}
    )
    ct = me.encrypt(pk, R, ek, msg)
    t_dec = bench(
        "me.decrypt(pk, dk, S, ct)",
        "from __main__ import me, pk, dk, S, ct",
        globals_dict={'me': me, 'pk': pk, 'dk': dk, 'S': S, 'ct': ct}
    )

    t_pair = bench(
        "pair(g, g)",
        "from charm.toolbox.pairinggroup import pair, G1; from __main__ import group; g=group.random(G1)",
        globals_dict={'group': group, 'pair': pair, 'G1': G1}
    )
    t_exp = bench(
        "z * g",
        "from charm.toolbox.pairinggroup import ZR, G1; from __main__ import group; z=group.random(ZR); g=group.random(G1)",
        globals_dict={'group': group, 'ZR': ZR, 'G1': G1}
    )
    t_hash = bench(
        "me.H(R)",
        "from __main__ import me, R",
        globals_dict={'me': me, 'R': R}
    )

    print(f"Setup  : {t_setup:.3f} ms")
    print(f"SKGen  : {t_skgen:.3f} ms")
    print(f"RKGen  : {t_rkgen:.3f} ms")
    print(f"Encrypt: {t_enc:.3f} ms")
    print(f"Decrypt: {t_dec:.3f} ms")
    print(f"Pairing: {t_pair:.3f} ms")
    print(f"Exp    : {t_exp:.3f} ms")
    print(f"Hash   : {t_hash:.3f} ms")