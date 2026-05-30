# Overview
This codebase evaluates the **proving and verification time** of Groth16 zero‑knowledge proofs for the PriME‑Deal attribute‑based matching protocol.  
All arithmetic is performed over the BN254 scalar field (`21888242871839275222246405745257275088548364400416034343698204186575808495617`).  
Pairing checks are executed off‑circuit (using Charm) while the circuit enforces **only Poseidon‑compatible arithmetic constraints** (attribute membership and share correctness).  
The benchmark varies the policy size \(n_b\), buyer attribute set size \(m\), threshold \(t_b\), Bloom‑filter usage, and false‑positive injection, then records proof generation and verification times in a CSV file.

---

## System Requirements (Tested Configuration)

- **CPU**: Intel Core i7‑11700 (2.50 GHz, 16 cores) or equivalent  
- **RAM**: 32 GB  
- **OS**: Ubuntu 20.04 LTS (any modern Linux distribution should work)  
- **Python**: 3.6.13 (Anaconda) with the `charm` virtual environment  
- **Node.js**: v22.13.0 or later (tested with v22.22.3)  
- **npm**: recent version (comes with Node.js)  
- **Circom**: 2.1.8 or compatible  
- **snarkjs**: 0.7.6 (locally installed via npm)  
- **Hardhat**: 2.19.0 (optional, not used by this benchmark)

---

## Python Environment & Dependencies

Activate the `charm` conda environment and verify installed packages:

```bash
conda activate charm
pip list
```
Key Python packages (should already be present in the charm environment):

Charm-Crypto 0.50

numpy 1.19.2

matplotlib 3.3.4

Standard libraries: hashlib, hmac, json, subprocess, csv, time, math, os, secrets

### Node.js & Circom Setup
Install Node.js (v22 or later) following official instructions.

Install circom and snarkjs globally or locally:

```bash
npm install -g circom@2.1.8 snarkjs@0.7.6
```
Verify versions:

```bash
circom --version
snarkjs --version
```

Inside the project root (where the Python script will run), install the circomlib npm package (required for the IsEqual template):

```bash
npm install circomlib
```

### Project Structure
text
.
├── prime_deal_ZKP_bn254.py   # Main benchmark script
├── performance.csv           # Output performance data (generated after run)
└── zkp_nb*_tb*_m*/           # Auto‑generated circuit directories (ignored by git)

All circuit artifacts `(.r1cs, .wasm, .zkey, etc.)` are created inside subdirectories named `zkp_nb{n_b}_tb{t_b}_m{m}`.

### How to Run
1. Ensure the `charm` Python environment is active and `circom/snarkjs` are in `$PATH`.

2. From the project root, execute:

```bash
python prime_deal_ZKP_bn254.py
```
The script will:

- Generate the required Circom circuit templates for each configuration.

- Compile them, perform the Groth16 trusted setup (Powers of Tau 2^14).

- For every parameter combination, run the matching protocol (off‑chain) and feed the witness into the prover.

- Print concise performance summaries on the terminal.

- Write all results to performance.csv with columns:

- - label (benchmark category)

- - n_b (policy size)

- - m (number of buyer attributes)

- - t_b (threshold)

- - use_filter (Boolean)

- - fake_count (number of false‑positive attributes)

- - rounds (how many successful proofs were averaged)

- - success (count of successful rounds)

- - avg_prove_ms (average proving time in milliseconds)

- - avg_verify_ms (average verification time in milliseconds)


### Interpreting the Output
- Terminal output: shows one line per configuration with average proving/verification times.
Example:

```text
policy_sm       n_b= 10 m= 5 t_b=3 filt=True fake= 0 | prove=123.45ms verify=4.56ms (3/3)
```
- CSV file: can be opened in Excel, Python, or LaTeX for further analysis and plotting.


### Notes for Reviewers
- The circuit fully respects the original protocol constraints:

- - Each `U0_a[i]` is proved to belong to the buyer’s attribute array `AB` exactly once.

- - `U0_u[i] === z_a[i] - nu_a[i]` holds for every revealed share.

- Pairing checks are performed outside the circuit by the Python‑Charm layer; the circuit only verifies the arithmetic relationship of the shares.

- Large integers (>2⁵³) are written as strings in the witness JSON to avoid JavaScript truncation.

- All snarkjs info logs are suppressed to keep the output clean; errors are still printed.

- The benchmark uses the same circuit size (number of constraints) as the original protocol; therefore timing results are representative of a real deployment.

## Troubleshooting
- `circom: command not found` → ensure `circom` is globally installed and $PATH includes its directory.

- `snarkjs: command not found` → similarly add `npx` or the global node_modules/.bin to $PATH, or run `npx snarkjs` directly (the script uses npx snarkjs).

- Witness generation fails with “Assert Failed” → verify that the Python environment uses the exact BN254 scalar field (printed at startup). If Charm returns a different order, hard‑coding P should fix it (already done in this script).

- Out of memory → reduce the large_nb configurations (e.g., skip 500) or increase Node.js heap size (NODE_OPTIONS="--max-old-space-size=8192").