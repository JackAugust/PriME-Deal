// SPDX-License-Identifier: MIT
pragma solidity >=0.7.0 <0.9.0;

import {Groth16Verifier} from "./Verifier_zkp_nb100_tb5_m20.sol";

contract PriMEDeal is Groth16Verifier {
    struct Listing {
        address payable seller;
        uint256 v;
        uint256 d;
        bool active;
    }

    mapping(bytes32 => Listing) public listings;

    event Listed(bytes32 indexed sid, address seller);
    event Bought(bytes32 indexed sid, address buyer);

    function list(bytes32 sid) external payable {
        require(!listings[sid].active, "Already listed");
        listings[sid] = Listing({
            seller: payable(msg.sender),
            v: msg.value,
            d: msg.value,
            active: true
        });
        emit Listed(sid, msg.sender);
    }

    // buy 使用继承的 verifyProof 进行 Groth16 验证
    function buy(
        bytes32 sid,
        uint[2] calldata a,
        uint[2][2] calldata b,
        uint[2] calldata c,
        uint[14] calldata input          // 固定长度 14
    ) external payable {
        Listing storage l = listings[sid];
        require(l.active, "Not active");
        require(msg.value == l.v, "Incorrect payment");
        require(verifyProof(a, b, c, input), "Invalid proof");

        l.active = false;
        (bool ok, ) = l.seller.call{value: msg.value}("");
        require(ok, "Transfer failed");
        emit Bought(sid, msg.sender);
    }
}