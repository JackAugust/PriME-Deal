#!/bin/bash
set -e

CIRCUIT="build/zkp_bench"
PTAU="pot13_final.ptau"
ZKEY_INIT="zkp_bench_init.zkey"
ZKEY_FINAL="zkp_bench.zkey"
VKEY="verification_key.json"
PROOF="proof.json"
PUBLIC="public.json"

# 1. 生成 witness
if [ ! -f witness.wtns ]; then
    echo "==> Generating witness..."
    echo '{"in": "12345"}' > input.json
    node ${CIRCUIT}_js/generate_witness.js ${CIRCUIT}_js/zkp_bench.wasm input.json witness.wtns
fi

# 2. 创建本地 powers of tau (13)
if [ ! -f "$PTAU" ]; then
    echo "==> Creating new powers of tau file (power 13)..."
    npx snarkjs powersoftau new bn128 13 pot13_0000.ptau -v
    echo "==> Adding first contribution..."
    echo "dummy" | npx snarkjs powersoftau contribute pot13_0000.ptau "$PTAU" --name="First" -v
fi

# 3. Groth16 设置
if [ ! -f "$ZKEY_INIT" ]; then
    echo "==> Running Groth16 setup..."
    npx snarkjs groth16 setup "$CIRCUIT.r1cs" "$PTAU" "$ZKEY_INIT"
fi

# 4. 贡献
if [ ! -f "$ZKEY_FINAL" ]; then
    echo "==> Contributing to phase 2..."
    echo "dummy" | npx snarkjs zkey contribute "$ZKEY_INIT" "$ZKEY_FINAL" --name="1st" -v
fi

# 5. 导出验证密钥
if [ ! -f "$VKEY" ]; then
    echo "==> Exporting verification key..."
    npx snarkjs zkey export verificationkey "$ZKEY_FINAL" "$VKEY"
fi

# 6. 生成证明并计时
echo "==> Generating proof..."
start_prove=$(date +%s%N)
npx snarkjs groth16 prove "$ZKEY_FINAL" witness.wtns "$PROOF" "$PUBLIC"
end_prove=$(date +%s%N)
prove_ms=$(( (end_prove - start_prove) / 1000000 ))

# 7. 验证证明并计时
echo "==> Verifying proof..."
start_verify=$(date +%s%N)
npx snarkjs groth16 verify "$VKEY" "$PUBLIC" "$PROOF"
end_verify=$(date +%s%N)
verify_ms=$(( (end_verify - start_verify) / 1000000 ))

# 8. 输出
constraints=$(npx snarkjs r1cs info "$CIRCUIT.r1cs" | grep "Constraints:" | awk '{print $2}')
proof_size=$(wc -c < "$PROOF")
echo ""
echo "=========== Results ==========="
echo "Circuit constraints: $constraints"
echo "Prove time: ${prove_ms} ms"
echo "Verify time: ${verify_ms} ms"
echo "Proof size: ${proof_size} bytes"
echo "==============================="