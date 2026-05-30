import subprocess, time, os, json

def setup(circuit_path="buyer.circom", output_dir="zkp"):
    """编译电路 + 可信设置 (powers of tau + groth16)"""
    os.makedirs(output_dir, exist_ok=True)
    # 编译
    subprocess.run(f"circom {circuit_path} --r1cs --wasm --sym -o {output_dir}", shell=True, check=True)
    # Powers of Tau (简化版，只做一次)
    subprocess.run(f"snarkjs powersoftau new bn128 12 {output_dir}/pot12_0000.ptau -v", shell=True, check=True)
    subprocess.run(f"snarkjs powersoftau contribute {output_dir}/pot12_0000.ptau {output_dir}/pot12_0001.ptau --name='first' -v -e='random'", shell=True, check=True)
    subprocess.run(f"snarkjs powersoftau prepare phase2 {output_dir}/pot12_0001.ptau {output_dir}/pot12_final.ptau -v", shell=True, check=True)
    # Groth16 setup
    subprocess.run(f"snarkjs groth16 setup {output_dir}/buyer.r1cs {output_dir}/pot12_final.ptau {output_dir}/buyer_0000.zkey", shell=True, check=True)
    subprocess.run(f"snarkjs zkey contribute {output_dir}/buyer_0000.zkey {output_dir}/buyer_final.zkey --name='contrib' -v -e='random2'", shell=True, check=True)
    subprocess.run(f"snarkjs zkey export verificationkey {output_dir}/buyer_final.zkey {output_dir}/verification_key.json", shell=True, check=True)

def prove(witness_json, output_dir="zkp"):
    """生成证明"""
    with open(f"{output_dir}/witness.json", "w") as f:
        json.dump(witness_json, f)
    subprocess.run(f"node {output_dir}/buyer_js/generate_witness.js {output_dir}/buyer_js/buyer.wasm {output_dir}/witness.json {output_dir}/witness.wtns", shell=True, check=True)
    start = time.time()
    subprocess.run(f"snarkjs groth16 prove {output_dir}/buyer_final.zkey {output_dir}/witness.wtns {output_dir}/proof.json {output_dir}/public.json", shell=True, check=True)
    prove_time = time.time() - start
    return prove_time

def verify(output_dir="zkp"):
    """验证证明"""
    start = time.time()
    subprocess.run(f"snarkjs groth16 verify {output_dir}/verification_key.json {output_dir}/public.json {output_dir}/proof.json", shell=True, check=True)
    verify_time = time.time() - start
    return verify_time