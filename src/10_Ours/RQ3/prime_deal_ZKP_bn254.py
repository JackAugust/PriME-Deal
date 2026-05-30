#!/usr/bin/env python3
"""
PriME‑Deal ZKP Performance on BN254 (Groth16) — Final Corrected
================================================================
- Scalar field: standard BN254 order
- All large ints in witness JSON are strings to avoid JS truncation
- Circuit constraints fully restored (isEqSums === 1, U0_u === z_a - nu_a)
- snarkJS logs suppressed, results saved to performance.csv
"""
import time, secrets, random, hashlib, hmac, math, os, json, subprocess, sys, csv
from charm.toolbox.pairinggroup import PairingGroup, ZR, G1, G2, GT, pair

# ===================== 环境配置 =====================
CIRCOM_CMD = "circom"
SNARKJS_CMD = "npx snarkjs"

# ===================== 曲线初始化（仅用于群运算） =====================
group = PairingGroup('BN254')
order_charm = group.order()          # Charm 内部阶（可能与标准不同，不用于标量运算）
g1 = group.random(G1)
g2 = group.random(G2)

# ===================== BN254 标准标量域 =====================
P = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# ===================== 工具函数 =====================
def modinv(a, m):
    g, x, _ = egcd(a % m, m)
    if g != 1: raise ValueError
    return x % m

def egcd(a, b):
    if a == 0: return b, 0, 1
    g, x1, y1 = egcd(b % a, a)
    return g, y1 - (b // a) * x1, x1

def H1(x: str):
    """Hash to G2, still uses Charm."""
    return group.hash(x, G2)

def H2(gt_elem):
    """Hash GT element to scalar (mod P)."""
    return int.from_bytes(hashlib.sha256(group.serialize(gt_elem)).digest()[:16], 'big') % P

def H3_scalar(x):
    """Hash any string/int to scalar field (mod P)."""
    if isinstance(x, int):
        x = str(x).encode()
    elif isinstance(x, str):
        x = x.encode()
    return int.from_bytes(hashlib.sha256(x).digest(), 'big') % P

def H3_zr(x: str):
    """Hash to ZR element (used only for Charm group exponents)."""
    return group.hash(str(x), ZR)

def H4(data):
    if isinstance(data, int): data = str(data).encode()
    elif isinstance(data, str): data = data.encode()
    return hashlib.sha256(data).digest()

def PRF(seed, label):
    return int.from_bytes(hmac.new(seed, label.encode(), hashlib.sha256).digest()[:16], 'big') % P

class ShamirSS:
    def __init__(self): self.P = P
    def share(self, secret, t, eval_pts):
        coeffs = [secret] + [secrets.randbelow(P) for _ in range(t-1)]
        return [(x, sum(c * pow(x, i, P) for i, c in enumerate(coeffs)) % P) for x in eval_pts], coeffs
    def reconstruct(self, shares):
        res = 0
        for j, (xj, yj) in enumerate(shares):
            prod = 1
            for i, (xi, _) in enumerate(shares):
                if i == j: continue
                diff = (xi - xj) % P
                if diff == 0: raise ValueError
                prod = (prod * xi * modinv(diff, P)) % P
            res = (res + yj * prod) % P
        return res

class DictOKVS:
    def __init__(self, y_pairs, seed):
        self.map = {k: v % P for k, v in y_pairs}
        self.seed = seed
    def decode(self, key):
        return self.map.get(key, PRF(self.seed, key))

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
        for idx in self._hashes(data): self.bits[idx//8] |= 1 << (idx % 8)
    def lookup(self, data):
        return all((self.bits[idx//8] >> (idx % 8)) & 1 for idx in self._hashes(data))

# ===================== 卖方模拟 =====================
def seller_simulate(n_b, t_b, mpk, sk_S, uid_S="seller"):
    sid = uid_S + "_" + str(int(time.time()*1000))
    tau = secrets.randbelow(P)                  # 秘密 (标量域)
    rho = secrets.randbelow(order_charm)
    rho_zr = group.init(ZR, rho)
    C0 = g1 ** rho_zr
    s_nu = secrets.token_bytes(16)
    s_r = secrets.token_bytes(16)

    policy = [f"attr_{i}" for i in range(n_b)]
    x_vals = [H3_scalar(p) for p in policy]     # 属性哈希 → 标量域

    shamir = ShamirSS()
    shares, _ = shamir.share(tau, t_b, x_vals)
    share_map = dict(zip(x_vals, [v for _, v in shares]))

    C_list = []
    y_pairs = []
    for p in policy:
        x = H3_scalar(p)
        s_i = share_map[x]
        r_i = secrets.randbelow(order_charm)
        r_zr = group.init(ZR, r_i)
        C_i = g1 ** r_zr
        K_i = H2(pair(H1(p), mpk) ** r_zr)
        tag_i = H4(K_i)
        nu_i = PRF(s_nu, p)
        y_i = (s_i + nu_i + H3_scalar(K_i)) % P
        C_list.append((C_i, tag_i))
        y_pairs.append((p, y_i))

    okvs = DictOKVS(y_pairs, s_nu)
    bf = BloomFilter(int(n_b*1.5), 0.001)
    for p in policy:
        bf.insert(group.serialize(group.hash(str(p), ZR)))

    S0 = H1(sid + str(tau)) ** sk_S
    D_vec = [okvs.decode(p) if okvs.decode(p) else PRF(s_nu, p) for p in policy]

    return {'sid': sid, 'C0': C0, 'C': C_list, 'okvs': okvs, 'filter': bf,
            'S0': S0, 's_nu': s_nu, 'tau': tau, 'policy': policy, 'D_vec': D_vec}

# ===================== 买方重构 =====================
def buyer_reconstruct(pp, buyer_attrs, dk_dict, seller_data, t_b, use_filter=True):
    pk_S, S0, sid, s_nu, okvs, C_list, bf, policy_set = (
        pp['pk_S'], seller_data['S0'], seller_data['sid'], seller_data['s_nu'],
        seller_data['okvs'], seller_data['C'], seller_data['filter'], set(seller_data['policy'])
    )
    filtered, fp = [], 0
    for a in buyer_attrs:
        if use_filter:
            if bf.lookup(group.serialize(group.hash(str(a), ZR))):
                filtered.append(a)
                if a not in policy_set: fp += 1
        else:
            filtered.append(a)

    pairings, shares, shares_zkp = 0, [], []
    for a in filtered:
        z = okvs.decode(a)
        nu = PRF(s_nu, a)
        D_a = dk_dict[a]
        for C_i, tag_i in C_list:
            Kp = H2(pair(C_i, D_a))
            pairings += 1
            if H4(Kp) == tag_i:
                u = (z - nu - H3_scalar(Kp)) % P
                shares.append((a, u))
                shares_zkp.append((a, u, H3_scalar(Kp)))
                break

    if len(shares) < t_b:
        return {'ok': False, 'shares': shares, 'tau_prime': None}

    shamir = ShamirSS()
    try:
        tau_c = shamir.reconstruct([(H3_scalar(a), u) for a, u in shares][:t_b])
    except ValueError:
        return {'ok': False, 'shares': shares, 'tau_prime': None}

    lhs = pair(S0, g1)
    rhs = pair(H1(sid + str(tau_c)), pk_S)
    ok = (lhs == rhs)
    return {'ok': ok, 'shares': shares, 'shares_zkp': shares_zkp, 'tau_prime': tau_c if ok else None}

# ===================== 电路生成（完整约束） =====================
def generate_circuit(NB, TB, M, output_path):
    lib_path = os.path.join(os.getcwd(), "node_modules", "circomlib", "circuits")
    code = 'pragma circom 2.0.0;\n\n'
    code += 'include "' + lib_path + '/comparators.circom";\n\n'
    code += 'template BuyerCircuit() {\n'

    # 公开输入
    code += '    signal input sid;\n'
    code += '    signal input com_AB;\n'
    code += '    signal input h_D;\n'
    code += '    signal input s_nu;\n'
    code += '    signal input t_b;\n'
    code += '    signal input S0_x_re;\n'
    code += '    signal input S0_x_im;\n'
    code += '    signal input S0_y_re;\n'
    code += '    signal input S0_y_im;\n'
    code += '    signal input mpk_x;\n'
    code += '    signal input mpk_y;\n'
    code += '    signal input pk_S_x;\n'
    code += '    signal input pk_S_y;\n'
    code += '    signal input uid_S;\n\n'

    # 私有见证
    code += '    signal input AB[' + str(M) + '];\n'
    code += '    signal input omega_B;\n'
    code += '    signal input uid_B;\n'
    code += '    signal input tau_prime;\n'
    code += '    signal input tau_calc;\n'
    code += '    signal input U0_a[' + str(TB) + '];\n'
    code += '    signal input U0_u[' + str(TB) + '];\n'
    code += '    signal input z_a[' + str(TB) + '];\n'
    code += '    signal input nu_a[' + str(TB) + '];\n'
    code += '    signal input D[' + str(NB) + '];\n'
    code += '    signal input cred_x_re;\n'
    code += '    signal input cred_x_im;\n'
    code += '    signal input cred_y_re;\n'
    code += '    signal input cred_y_im;\n\n'

    # 约束：属性匹配 + 份额等式
    code += '    signal isEqSums[' + str(TB) + '];\n'
    code += '    component eq_comps[' + str(TB) + '][' + str(M) + '];\n'
    code += '    signal eq_outs[' + str(TB) + '][' + str(M) + '];\n'

    code += '    for (var i = 0; i < ' + str(TB) + '; i++) {\n'
    code += '        for (var j = 0; j < ' + str(M) + '; j++) {\n'
    code += '            eq_comps[i][j] = IsEqual();\n'
    code += '            eq_comps[i][j].in[0] <== U0_a[i];\n'
    code += '            eq_comps[i][j].in[1] <== AB[j];\n'
    code += '            eq_outs[i][j] <== eq_comps[i][j].out;\n'
    code += '        }\n'
    sum_eq = ' + '.join(['eq_outs[i][' + str(j) + ']' for j in range(M)])
    code += '        isEqSums[i] <== ' + sum_eq + ';\n'
    code += '        isEqSums[i] === 1;\n'
    code += '        U0_u[i] === z_a[i] - nu_a[i];\n'
    code += '    }\n\n'

    code += '    tau_prime === tau_calc;\n\n'
    code += '}\n\n'
    code += 'component main { public [ sid, com_AB, h_D, s_nu, t_b, '
    code += 'S0_x_re, S0_x_im, S0_y_re, S0_y_im, '
    code += 'mpk_x, mpk_y, pk_S_x, pk_S_y, uid_S ] } = BuyerCircuit();\n'

    with open(output_path, "w") as f:
        f.write(code)
    print(f"Circuit written to {output_path}")

# ===================== 可信设置（抑制日志） =====================
def setup(circuit_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    base = os.path.splitext(os.path.basename(circuit_path))[0]
    subprocess.run(f"{CIRCOM_CMD} {circuit_path} --r1cs --wasm --sym -o {output_dir}",
                   shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    ptau = f"{output_dir}/pot14_final.ptau"
    if not os.path.exists(ptau):
        subprocess.run(f"{SNARKJS_CMD} powersoftau new bn128 14 {output_dir}/pot14_0000.ptau -v",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(f"{SNARKJS_CMD} powersoftau contribute {output_dir}/pot14_0000.ptau {output_dir}/pot14_0001.ptau --name='first' -v -e='random'",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(f"{SNARKJS_CMD} powersoftau prepare phase2 {output_dir}/pot14_0001.ptau {ptau} -v",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    zkey = f"{output_dir}/{base}_final.zkey"
    if not os.path.exists(zkey):
        subprocess.run(f"{SNARKJS_CMD} groth16 setup {output_dir}/{base}.r1cs {ptau} {output_dir}/{base}_0000.zkey",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(f"{SNARKJS_CMD} zkey contribute {output_dir}/{base}_0000.zkey {zkey} --name='contrib' -v -e='random2'",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        subprocess.run(f"{SNARKJS_CMD} zkey export verificationkey {zkey} {output_dir}/verification_key.json",
                       shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return base

def prove(witness_dict, output_dir, circuit_base):
    js_dir = f"{output_dir}/{circuit_base}_js"
    wasm = f"{js_dir}/{circuit_base}.wasm"
    witness_json = f"{output_dir}/witness.json"
    witness_wtns = f"{output_dir}/witness.wtns"
    with open(witness_json, "w") as f:
        json.dump(witness_dict, f, indent=2)
    subprocess.run(f"node {js_dir}/generate_witness.js {wasm} {witness_json} {witness_wtns}",
                   shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    start = time.time()
    subprocess.run(f"{SNARKJS_CMD} groth16 prove {output_dir}/{circuit_base}_final.zkey {witness_wtns} {output_dir}/proof.json {output_dir}/public.json",
                   shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return time.time() - start

def verify(output_dir):
    start = time.time()
    subprocess.run(f"{SNARKJS_CMD} groth16 verify {output_dir}/verification_key.json {output_dir}/public.json {output_dir}/proof.json",
                   shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    return time.time() - start

# ===================== 坐标转换（占位） =====================
def g1_coords(elem):
    ser = group.serialize(elem)
    return int.from_bytes(ser[:32], 'big'), int.from_bytes(ser[32:64], 'big')

def g2_coords(elem):
    return (0, 0, 0, 0)   # 配对验证不进入电路，填0不影响证明

# ===================== 准备 witness（大整数转字符串） =====================
def prepare_witness(sid, com_AB, h_D, s_nu, t_b, S0_coords, mpk_coords, pk_S_coords, uid_S,
                    AB_ints, omega_B, uid_B, tau_prime, tau_calc, U0, D_vec, cred_coords, z_ints, nu_ints):
    def to_str(x):
        """Convert large ints to string to avoid JSON truncation."""
        return str(x) if isinstance(x, int) and (x > 2**53 or x < -2**53) else x

    return {
        "sid": to_str(int(sid) if isinstance(sid, int) else int.from_bytes(str(sid).encode(), 'big') % P),
        "com_AB": to_str(int(com_AB) % P),
        "h_D": to_str(int(h_D) % P),
        "s_nu": to_str(int.from_bytes(s_nu, 'big') % P),
        "t_b": t_b,
        "S0_x_re": to_str(int(S0_coords[0]) % P),
        "S0_x_im": to_str(int(S0_coords[1]) % P),
        "S0_y_re": to_str(int(S0_coords[2]) % P),
        "S0_y_im": to_str(int(S0_coords[3]) % P),
        "mpk_x": to_str(int(mpk_coords[0]) % P),
        "mpk_y": to_str(int(mpk_coords[1]) % P),
        "pk_S_x": to_str(int(pk_S_coords[0]) % P),
        "pk_S_y": to_str(int(pk_S_coords[1]) % P),
        "uid_S": to_str(int.from_bytes(str(uid_S).encode(), 'big') % P),
        "AB": [to_str(int(x) % P) for x in AB_ints],
        "omega_B": to_str(int(omega_B) % P),
        "uid_B": to_str(int.from_bytes(str(uid_B).encode(), 'big') % P),
        "tau_prime": to_str(int(tau_prime) % P),
        "tau_calc": to_str(int(tau_calc) % P),
        "U0_a": [to_str(int(a) % P) for a,_ in U0],
        "U0_u": [to_str(int(u) % P) for _,u in U0],
        "z_a": [to_str(int(z) % P) for z in z_ints],
        "nu_a": [to_str(int(nu) % P) for nu in nu_ints],
        "D": [to_str(int(d) % P) for d in D_vec],
        "cred_x_re": to_str(int(cred_coords[0]) % P),
        "cred_x_im": to_str(int(cred_coords[1]) % P),
        "cred_y_re": to_str(int(cred_coords[2]) % P),
        "cred_y_im": to_str(int(cred_coords[3]) % P)
    }

# ===================== ZKP 测试主循环 =====================
def run_zkp_config(n_b, m, t_b, rounds, use_filter, fake_count, label, setup_cache):
    key = (n_b, t_b, m)
    if key not in setup_cache:
        zkp_dir = f"zkp_nb{n_b}_tb{t_b}_m{m}"
        circuit_file = f"buyer_nb{n_b}_tb{t_b}_m{m}.circom"
        generate_circuit(n_b, t_b, m, circuit_file)
        base = setup(circuit_file, zkp_dir)
        setup_cache[key] = (zkp_dir, base)
    else:
        zkp_dir, base = setup_cache[key]

    total_prove = total_verify = 0.0
    success = 0
    for r in range(rounds):
        # ---- 群密钥生成 (Charm 域) ----
        s = secrets.randbelow(order_charm)
        s_zr = group.init(ZR, s)
        mpk = g1 ** s_zr
        sk_S = s_zr * H3_zr("seller")
        pp = {'pk_S': g1 ** sk_S}

        # ---- 卖方模拟 ----
        seller_data = seller_simulate(n_b, t_b, mpk, sk_S)

        policy = seller_data['policy']
        overlap = min(t_b, n_b)
        common = random.sample(policy, overlap)
        extra_req = [f"req_{i}" for i in range(m - overlap)]

        buyer_attrs_base = set(common + extra_req)
        buyer_attrs_filter = set(buyer_attrs_base)
        if fake_count > 0:
            buyer_attrs_filter.update({f"fake_{i}" for i in range(fake_count)})

        dk = {a: H1(a) ** s_zr for a in buyer_attrs_filter}
        res = buyer_reconstruct(pp, buyer_attrs_filter, dk, seller_data, t_b, use_filter)
        if not res['ok']:
            continue

        # ---- 构造电路见证 ----
        AB_sorted = sorted(buyer_attrs_base, key=lambda x: H3_scalar(x))
        AB_ints = [H3_scalar(a) for a in AB_sorted]   # 长度固定为 m

        omega_B = secrets.randbelow(P)
        com_AB = int.from_bytes(H4(''.join(AB_sorted) + str(omega_B)), 'big') % P
        D_vec = seller_data['D_vec']
        h_D = int.from_bytes(H4(str(D_vec).encode()), 'big') % P
        uid_B = "buyer_" + str(r)
        cred = H1(uid_B + ''.join(sorted(buyer_attrs_base))) ** s_zr

        shares_zkp = res['shares_zkp'][:t_b]
        okvs_map = seller_data['okvs'].map
        U0 = []
        z_ints = []
        nu_ints = []
        for a, u, h3kp in shares_zkp:
            U0.append((H3_scalar(a), u))
            z = okvs_map[a]
            nu_a = (PRF(seller_data['s_nu'], a) + h3kp) % P
            z_ints.append(z)
            nu_ints.append(nu_a)

        witness = prepare_witness(
            sid=seller_data['sid'], com_AB=com_AB, h_D=h_D, s_nu=seller_data['s_nu'], t_b=t_b,
            S0_coords=g2_coords(seller_data['S0']), mpk_coords=g1_coords(mpk),
            pk_S_coords=g1_coords(pp['pk_S']), uid_S="seller",
            AB_ints=AB_ints, omega_B=omega_B, uid_B=uid_B,
            tau_prime=res['tau_prime'], tau_calc=res['tau_prime'],
            U0=U0, D_vec=D_vec, cred_coords=g2_coords(cred),
            z_ints=z_ints, nu_ints=nu_ints
        )

        try:
            p_time = prove(witness, zkp_dir, base)
            v_time = verify(zkp_dir)
            total_prove += p_time
            total_verify += v_time
            success += 1
        except Exception as e:
            print(f"  [Error] round {r}: {e}")

    if success:
        avg_p = (total_prove / success) * 1000
        avg_v = (total_verify / success) * 1000
        print(f"{label:15s} n_b={n_b:3d} m={m:2d} t_b={t_b} filt={use_filter} fake={fake_count:2d} | "
              f"prove={avg_p:.2f}ms verify={avg_v:.2f}ms ({success}/{rounds})")
        return {
            'label': label, 'n_b': n_b, 'm': m, 't_b': t_b,
            'use_filter': use_filter, 'fake_count': fake_count,
            'rounds': rounds, 'success': success,
            'avg_prove_ms': avg_p, 'avg_verify_ms': avg_v
        }
    else:
        print(f"{label:15s} n_b={n_b:3d} m={m:2d} t_b={t_b} filt={use_filter} fake={fake_count:2d} | NO SUCCESS")
        return {
            'label': label, 'n_b': n_b, 'm': m, 't_b': t_b,
            'use_filter': use_filter, 'fake_count': fake_count,
            'rounds': rounds, 'success': 0,
            'avg_prove_ms': None, 'avg_verify_ms': None
        }

# ===================== 入口 =====================
def main():
    print("PriME‑Deal ZKP Performance on BN254\n")
    setup_cache = {}
    results = []

    # sweeps_small = [
    #     ('policy_sm', [(n_b, 5, 3) for n_b in [10, 20, 30, 50]]),
    #     ('attrs_sm',  [(20, m, 3) for m in [3, 5, 7, 10]]),
    #     ('threshold_sm', [(20, 5, t_b) for t_b in [2, 3, 4, 5]]),
    # ]
    # for sweep, configs in sweeps_small:
    #     for n_b, m, t_b in configs:
    #         for use_f in [True, False]:
    #             res = run_zkp_config(n_b, m, t_b, rounds=3, use_filter=use_f, fake_count=0,
    #                                  label=sweep, setup_cache=setup_cache)
    #             results.append(res)

    print("\n--- Large scale ---")
    for n_b in [500]:
        res = run_zkp_config(n_b, 50, 5, rounds=2, use_filter=True, fake_count=0,
                             label="large_nb", setup_cache=setup_cache)
        results.append(res)
    # for m in [20, 30, 50]:
    #     res = run_zkp_config(200, m, 5, rounds=2, use_filter=True, fake_count=0,
    #                          label="large_m", setup_cache=setup_cache)
    #     results.append(res)

    # print("\n--- False‑positive stress ---")
    # for fake in [0, 10, 20, 50]:
    #     res = run_zkp_config(200, 20, 5, rounds=2, use_filter=True, fake_count=fake,
    #                          label="fp_stress", setup_cache=setup_cache)
    #     results.append(res)

    # 写入 CSV
    csv_file = "performance.csv"
    fieldnames = ['label', 'n_b', 'm', 't_b', 'use_filter', 'fake_count',
                  'rounds', 'success', 'avg_prove_ms', 'avg_verify_ms']
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"\nPerformance data written to {csv_file}")

if __name__ == "__main__":
    main()