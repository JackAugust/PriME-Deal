const snarkjs = require("snarkjs");
const fs = require("fs");
const path = require("path");

async function run() {
    // 文件路径
    const r1csPath = "build/zkp_bench.r1cs";
    const wasmPath = "build/zkp_bench_js/zkp_bench.wasm";
    const ptauPath = "pot12_final.ptau";           // 12次幂足够 5000 约束
    const zkeyPath = "zkp_bench.zkey";
    const proofPath = "proof.json";
    const publicPath = "public.json";

    // 1. 准备输入
    const input = { in: 12345 };
    console.log("Generating witness...");
    const startWitness = Date.now();
    const witness = await snarkjs.wtns.calculate(input, wasmPath);
    console.log(`Witness generated in ${Date.now() - startWitness} ms`);

    // 2. 下载 ptau（如果不存在）
    if (!fs.existsSync(ptauPath)) {
        console.log("Downloading powers of tau file...");
        const url = "https://hermez.s3-eu-west-1.amazonaws.com/powersOfTau28_hez_final_12.ptau";
        await snarkjs.powersOfTau.download(12, ptauPath, url, console.log);
        console.log("Downloaded.");
    }

    // 3. Groth16 设置（如果 zkey 不存在）
    if (!fs.existsSync(zkeyPath)) {
        console.log("Running Groth16 setup...");
        const startSetup = Date.now();
        await snarkjs.groth16.setup(r1csPath, ptauPath, zkeyPath, console);
        console.log(`Setup done in ${Date.now() - startSetup} ms`);
    } else {
        console.log("Using existing zkey.");
    }

    // 4. 导出验证密钥
    const vk = await snarkjs.zKey.exportVerificationKey(zkeyPath, console);
    console.log("Verification key exported.");

    // 5. 生成证明并计时
    console.log("Generating proof...");
    const startProve = Date.now();
    const { proof, publicSignals } = await snarkjs.groth16.prove(zkeyPath, witness, console);
    const proveTime = Date.now() - startProve;
    console.log(`Prove time: ${proveTime} ms`);
    fs.writeFileSync(proofPath, JSON.stringify(proof, null, 2));
    fs.writeFileSync(publicPath, JSON.stringify(publicSignals, null, 2));
    console.log(`Proof size: ${JSON.stringify(proof).length} bytes`);

    // 6. 验证证明并计时
    console.log("Verifying proof...");
    const startVerify = Date.now();
    const valid = await snarkjs.groth16.verify(vk, publicSignals, proof, console);
    const verifyTime = Date.now() - startVerify;
    console.log(`Verify time: ${verifyTime} ms, valid: ${valid}`);

    // 7. 约束数
    const info = await snarkjs.r1cs.info(r1csPath);
    console.log(`Constraints: ${info.nConstraints}`);
}

run().catch(console.error);