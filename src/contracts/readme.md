# PriME‑Deal SC Benchmark and ZKP Benchmark Reproduction

## Hardware & Software Requirements
- CPU: Intel Core i7‑11700 (2.50 GHz, 16 cores) or equivalent
- RAM: 32 GB
- OS: Ubuntu 20.04 LTS (any Linux distribution should work)
- Node.js: v22.13.0 or later (tested with v22.22.3)
- Circom: 2.1.8 or compatible
- snarkjs: 0.7.6 (locally installed via npm)
- npm
- Hardhat 2.19.0 (installed locally)

## PriME‑Deal Smart Contract Gas Benchmark
This guide reproduces the on‑chain gas consumption of the PriME‑Deal smart
contract (Algorithm 4 in the paper).

### Setup
```bash
cd /path/to/contracts
npm init -y
npm install --save-dev hardhat@2.19.0 @nomiclabs/hardhat-waffle @nomiclabs/hardhat-ethers ethers chai
```
#### Contract
Save the following Solidity code as `contracts/PriMEDeal.sol`:
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract PriMEDeal {
    struct Listing {
        address payable seller;
        bytes32 hD;
        bytes32 comPB;
        uint256 tb;
        bytes32 hk2;
        bytes32 root;
        bytes32 sigmaRoot;
        bytes32 S0;
        uint256 v;
        uint256 d;
        uint8 status;
        uint256 timer;
        bytes32 k2;
    }
    mapping(bytes32 => Listing) public listings;
    // ... (full contract from the paper's Algorithm 4)
    function verifyGroth16(bytes calldata proof, bytes calldata input) internal view returns (bool) {
        uint256[24] memory m;
        bool success;
        assembly {
            success := staticcall(gas(), 0x08, add(input.offset,32), mload(input.offset), m, 0x180)
        }
        return success;
    }
    // ... (test helper functions)
}
```
### Hardhat Configuration
Create `hardhat.config.js` with:

```javascript
require("@nomiclabs/hardhat-waffle");
require("@nomiclabs/hardhat-ethers");
module.exports = {
  solidity: {
    version: "0.8.20",
    settings: { viaIR: true, optimizer: { enabled: true, runs: 200 } }
  },
  paths: { sources: "./", tests: "./test", cache: "./cache", artifacts: "./artifacts" }
};
// ...
```

### Test Script
Create `test/gas.js`:

```javascript
const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("PriMEDeal Gas", function () {
    let contract, seller, buyer;
    const sid = ethers.utils.formatBytes32String("trade123");
    const dummyB32 = ethers.utils.formatBytes32String("dummy");
    const proof = "0x" + "00".repeat(192);
    const input = "0x" + "0000".repeat(132); // dummy input
    before(async () => {
        [seller, buyer] = await ethers.getSigners();
        const PMD = await ethers.getContractFactory("PriMEDeal");
        contract = await PMD.deploy();
        await contract.deployed();
    });
    it("list gas", async () => {
        const tx = await contract.connect(seller).list(/*...*/);
        console.log(`list gas: ${(await tx.wait()).gasUsed}`);
    });
    // ... (similar for buy, reveal, challenge, isolated proof)
});
```

### Execution
```bash
npx hardhat compile
npx hardhat test
```

### Expected Output
```shell
$ npx hardhat test
  PriMEDeal Gas
list gas: 272896
    ✔ list gas (38ms)
buy (reverted) gas: 100689
    ✔ buy (proof verification) gas (43ms)
isolated proof verification gas: 69426 
    ✔ isolated proof verification gas
reveal core gas: 22471
    ✔ reveal core gas
challenge core gas: 43550
    ✔ challenge core gas
```
The measured `isolated proof verification gas` (69,426) corresponds to a
failed staticcall to the BN254 precompile. A successful Groth16
verification consumes approximately 250,000 gas (EIP‑197 standard).
The Benchmark ZKP of PriME‑Deal is as follows.


## PriME‑Deal ZKP Benchmark 
This guide reproduces the Groth16 proving and verification times for a circuit
with constraints representative of the buyer's compliance relation $\mathcal{R}_{\mathsf{buy}}$.

### 1. Install Circom Compiler
```bash
# Install Rust if not present
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source $HOME/.cargo/env

# Clone and build Circom
git clone https://github.com/iden3/circom.git
cd circom
cargo build --release
export PATH=$PATH:$(pwd)/target/release
cd ..
```

### 2. Install Node.js Dependencies
```bash
mkdir prime-zkp && cd prime-zkp
npm init -y
npm install circomlib snarkjs@0.7.6
```

### 3. Compile the Benchmark Circuit
Create `zkp_bench.circom` with the following content (a cascade of MulAdd gates that produces exactly 5000 constraints):
```circom
pragma circom 2.0.0;

template MulAdd() {
    signal input a, b, c;
    signal output out;
    out <== a * b + c;
}

template Cascade(N) {
    signal input in;
    signal output out;
    signal inter[N+1];
    inter[0] <== in;
    component ma[N];
    for (var i=0; i<N; i++) {
        ma[i] = MulAdd();
        ma[i].a <== inter[i];
        ma[i].b <== 2;
        ma[i].c <== i;
        inter[i+1] <== ma[i].out;
    }
    out <== inter[N];
}

component main = Cascade(5000);
```

Compile it:
```bash
circom zkp_bench.circom --r1cs --wasm --sym -o build
```

### 4. Run the Groth16 Benchmark
Create `run_zkp.sh` with the following content and make it executable (`chmod +x run_zkp.sh`):
```shell
#!/bin/bash
set -e
CIRCUIT="build/zkp_bench"
PTAU="pot14_final.ptau"
ZKEY_INIT="zkp_bench_init.zkey"
ZKEY_FINAL="zkp_bench.zkey"

# Generate witness
echo '{"in":"12345"}' > input.json
node ${CIRCUIT}_js/generate_witness.js ${CIRCUIT}_js/zkp_bench.wasm input.json witness.wtns

# Powers of Tau (14)
if [ ! -f "$PTAU" ]; then
  npx snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
  echo "dummy" | npx snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau --name="First" -v
  npx snarkjs powersoftau prepare phase2 pot14_0001.ptau "$PTAU" -v
fi

# Setup
if [ ! -f "$ZKEY_INIT" ]; then
  npx snarkjs groth16 setup "$CIRCUIT.r1cs" "$PTAU" "$ZKEY_INIT" -v
fi

# Contribute
if [ ! -f "$ZKEY_FINAL" ]; then
  echo "dummy" | npx snarkjs zkey contribute "$ZKEY_INIT" "$ZKEY_FINAL" --name="1st" -v
fi

# Prove
echo "=== Proving ==="
/usr/bin/time -f "Prove time (real): %e s" npx snarkjs groth16 prove "$ZKEY_FINAL" witness.wtns proof.json public.json

# Verify
echo "=== Verifying ==="
/usr/bin/time -f "Verify time (real): %e s" npx snarkjs groth16 verify verification_key.json public.json proof.json

# Constraint count
npx snarkjs r1cs info "$CIRCUIT.r1cs"
```

Execute:
```bash
./run_zkp.sh
```

### Expected Output
```shell
$ rm -f zkp_bench_init.zkey zkp_bench.zkey witness.wtns proof.json public.json

$ echo '{"in": "12345"}' > input.json

$ node build/zkp_bench_js/generate_witness.js build/zkp_bench_js/zkp_bench.wasm input.json witness.wtns

$ npx snarkjs powersoftau new bn128 14 pot14_0000.ptau -v
[DEBUG] snarkJS: Calculating First Challenge Hash
[DEBUG] snarkJS: Calculate Initial Hash: tauG1
[DEBUG] snarkJS: Calculate Initial Hash: tauG2
[DEBUG] snarkJS: Calculate Initial Hash: alphaTauG1
[DEBUG] snarkJS: Calculate Initial Hash: betaTauG1
[DEBUG] snarkJS: Blank Contribution Hash:
		786a02f7 42015903 c6c6fd85 2552d272
		912f4740 e1584761 8a86e217 f71f5419
		d25e1031 afee5853 13896444 934eb04b
		903a685b 1448b755 d56f701a fe9be2ce
[INFO]  snarkJS: First Contribution Hash:
		bc0bde79 80381fa6 42b20975 91dd83f1
		ed15b003 e15c3552 0af32c95 eb519149
		2a6f3175 215635cf c10e6098 e2c612d0
		ca84f1a9 f90b5333 560c8af5 9b9209f4

$ echo "dummy" | npx snarkjs powersoftau contribute pot14_0000.ptau pot14_0001.ptau --name="First" -v
Enter a random text. (Entropy): dummy
[DEBUG] snarkJS: Calculating First Challenge Hash
[DEBUG] snarkJS: Calculate Initial Hash: tauG1
[DEBUG] snarkJS: Calculate Initial Hash: tauG2
[DEBUG] snarkJS: Calculate Initial Hash: alphaTauG1
[DEBUG] snarkJS: Calculate Initial Hash: betaTauG1
[DEBUG] snarkJS: processing: tauG1: 0/32767
[DEBUG] snarkJS: processing: tauG1: 16384/32767
[DEBUG] snarkJS: processing: tauG2: 0/16384
[DEBUG] snarkJS: processing: tauG2: 8192/16384
[DEBUG] snarkJS: processing: alphaTauG1: 0/16384
[DEBUG] snarkJS: processing: betaTauG1: 0/16384
[DEBUG] snarkJS: processing: betaTauG2: 0/1
[INFO]  snarkJS: Contribution Response Hash imported: 
		a0959390 af7fe034 2d63d473 2da75d97
		4d01024f f173d40e 88aa4cfe 0180c7ad
		e62d94e4 18549597 5be9537c d45f21ba
		54e42a0c fc1e5f5f da50ec43 76ab1a32
[INFO]  snarkJS: Next Challenge Hash: 
		a81af99d 2f56973b 3bbf3e68 95d4668d
		fe311ab5 ab16548d 23986b8c 777be774
		052f1aa3 8e787da7 b1600946 4cc1ac03
		121c5880 ac82ed95 c268b29e 19ca7931
$ npx snarkjs powersoftau prepare phase2 pot14_0001.ptau pot14_final.ptau -v
[DEBUG] snarkJS: Starting section: tauG1
[DEBUG] snarkJS: tauG1: fft 0 mix start: 0/1
[DEBUG] snarkJS: tauG1: fft 0 mix end: 0/1
[DEBUG] snarkJS: tauG1: fft 1 mix start: 0/1
....

$ echo "dummy" | npx snarkjs zkey contribute zkp_bench_init.zkey zkp_bench.zkey --name="1st" -v
Enter a random text. (Entropy): dummy
[DEBUG] snarkJS: Applying key: L Section: 0/5000
[DEBUG] snarkJS: Applying key: H Section: 0/8192
[INFO]  snarkJS: Circuit Hash: 
		4c51bca9 3175a86b de16fc90 9e2c7d29
		2022697c 425d055d e6894697 beb9ed02
		e99717ba e9de7226 96523b64 d8ca06f1
		cad7a06c 298d7e9a 989fcbdb 800c5318
[INFO]  snarkJS: Contribution Hash: 
		be4d2eb3 ecb41e5b 16fbbff3 a4ed18fa
		9a43e5aa 8924be44 b7b30429 3ae79713
		4fecbccf d18bce9e 3ad535ad e78409f7
		c14e4c4c 5047d981 0ae3e593 dee15a84

$ npx snarkjs zkey export verificationkey zkp_bench.zkey verification_key.json
[INFO]  snarkJS: EXPORT VERIFICATION KEY STARTED
[INFO]  snarkJS: > Detected protocol: groth16
[INFO]  snarkJS: EXPORT VERIFICATION KEY FINISHED

s$ time npx snarkjs groth16 prove zkp_bench.zkey witness.wtns proof.json public.json

real	0m0.818s
user	0m2.105s
sys	0m0.210s

$ time npx snarkjs groth16 verify verification_key.json public.json proof.json
[INFO]  snarkJS: OK!

real	0m0.640s
user	0m0.905s
sys	0m0.078s

$ npx snarkjs r1cs info build/zkp_bench.r1cs
[INFO]  snarkJS: Curve: bn-128
[INFO]  snarkJS: # of Wires: 5002
[INFO]  snarkJS: # of Constraints: 5000
[INFO]  snarkJS: # of Private Inputs: 1
[INFO]  snarkJS: # of Public Inputs: 0
[INFO]  snarkJS: # of Labels: 25004
[INFO]  snarkJS: # of Outputs: 1

```



