const { expect } = require("chai");
const { ethers } = require("hardhat");
const fs = require("fs");
const path = require("path");

describe("PriMEDeal Gas (real ZKP)", function () {
    let contract, seller, buyer;
    const sid = ethers.utils.formatBytes32String("trade1");

    // 从 src/contracts 出发，向上两级到项目根，再进入 zkp 目录
    const proofPath = path.join(__dirname, "../../../src/10_Ours/RQ3/ZKP/zkp_nb100_tb5_m20/proof.json");
    const publicPath = path.join(__dirname, "../../../src/10_Ours/RQ3/ZKP/zkp_nb100_tb5_m20/public.json");
    const proof = JSON.parse(fs.readFileSync(proofPath, "utf8"));
    const pub = JSON.parse(fs.readFileSync(publicPath, "utf8"));

    const a = [proof.pi_a[0], proof.pi_a[1]];
    const b = [
        [proof.pi_b[0][0], proof.pi_b[0][1]],
        [proof.pi_b[1][0], proof.pi_b[1][1]],
    ];
    const c = [proof.pi_c[0], proof.pi_c[1]];

    if (pub.length !== 14) {
        throw new Error(`Expected 14 public inputs, got ${pub.length}`);
    }

    before(async () => {
        [seller, buyer] = await ethers.getSigners();
        const PriMEDeal = await ethers.getContractFactory("PriMEDeal");
        contract = await PriMEDeal.deploy();
        await contract.deployed();
    });

    it("list gas", async () => {
        const tx = await contract.connect(seller).list(sid, {
            value: ethers.utils.parseEther("0.1")
        });
        const receipt = await tx.wait();
        console.log(`list gas: ${receipt.gasUsed.toString()}`);
    });

    it("buy gas (real Groth16 proof)", async () => {
        const tx = await contract.connect(buyer).buy(sid, a, b, c, pub, {
            value: ethers.utils.parseEther("0.1")
        });
        const receipt = await tx.wait();
        console.log(`buy gas: ${receipt.gasUsed.toString()}`);
    });
});