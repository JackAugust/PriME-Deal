// SPDX-License-Identifier: GPL-3.0
/*
    Copyright 2021 0KIMS association.

    This file is generated with [snarkJS](https://github.com/iden3/snarkjs).

    snarkJS is a free software: you can redistribute it and/or modify it
    under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    snarkJS is distributed in the hope that it will be useful, but WITHOUT
    ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
    or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
    License for more details.

    You should have received a copy of the GNU General Public License
    along with snarkJS. If not, see <https://www.gnu.org/licenses/>.
*/

pragma solidity >=0.7.0 <0.9.0;

contract Groth16Verifier {
    // Scalar field size
    uint256 constant r    = 21888242871839275222246405745257275088548364400416034343698204186575808495617;
    // Base field size
    uint256 constant q   = 21888242871839275222246405745257275088696311157297823662689037894645226208583;

    // Verification Key data
    uint256 constant alphax  = 9655447137264293045046307526071145689206715852231502168956624667036298542436;
    uint256 constant alphay  = 4956364058100063071273135363552215013206087856650482529837530113978778117763;
    uint256 constant betax1  = 5974636771732378703864118913345551308437043018052925626098526790111897570791;
    uint256 constant betax2  = 9248536823672229416466449016379267734190460032907629201530401251270396856373;
    uint256 constant betay1  = 11803016756427458307510581520157533831507768982575700555432534270009515837908;
    uint256 constant betay2  = 12109329127640590988559052231292366372415811207413201046861755217241867986316;
    uint256 constant gammax1 = 11559732032986387107991004021392285783925812861821192530917403151452391805634;
    uint256 constant gammax2 = 10857046999023057135944570762232829481370756359578518086990519993285655852781;
    uint256 constant gammay1 = 4082367875863433681332203403145435568316851327593401208105741076214120093531;
    uint256 constant gammay2 = 8495653923123431417604973247489272438418190587263600148770280649306958101930;
    uint256 constant deltax1 = 19137634248821824237200643790847449796115350362812155665318654785189604483942;
    uint256 constant deltax2 = 6975018978412135031504906249448111353600526679672450699493957317628091032419;
    uint256 constant deltay1 = 18296622211112630673368323326264715114267258737826726547402559955695816354845;
    uint256 constant deltay2 = 18081788571526832068645830404409182916384966514977223005546517344745787949040;

    
    uint256 constant IC0x = 10580708573215477774412528214959290343445022064145098414617051070807436087636;
    uint256 constant IC0y = 4178569191641065491757339345827771672959355250861266238957534800524074671383;
    
    uint256 constant IC1x = 9381244894832178750180347541430408839208480403979963987844807885988425330781;
    uint256 constant IC1y = 9618318594429763083472202191495950959260401313291292729932310663239216908261;
    
    uint256 constant IC2x = 11222423763963932503787615635640857530579463820863140957832722880724664945120;
    uint256 constant IC2y = 525726174979141888446876671565828485856229105476401185027161032393523968414;
    
    uint256 constant IC3x = 15121992811021515176477384882532520160902524480493182226833086284723167549215;
    uint256 constant IC3y = 391128834439663337397043643068271450577911197348107558642541892718137790408;
    
    uint256 constant IC4x = 12529841890338744144637945949525015211016243995669828819064514821021246739758;
    uint256 constant IC4y = 9480593689374659628077781281116172005750675872301540860017146941977479699845;
    
    uint256 constant IC5x = 3568663438317092552977973038195264771143609348687038291506570391798627141864;
    uint256 constant IC5y = 10539819817861771561546175321919649150475302915085307273138102891915897603957;
    
    uint256 constant IC6x = 2499681685073380288075877073004194153637893790245036901345329932595988545460;
    uint256 constant IC6y = 3955969586111398587578539176499610601579143003763390633829602079530028139029;
    
    uint256 constant IC7x = 5562983544004850751882570729783363972127931583204073357383327730417078150932;
    uint256 constant IC7y = 12152083193285867793947396344411535122115349047816727183995932952412241994978;
    
    uint256 constant IC8x = 14906613508950382790506772884784273716713436813059651951147098604592807708340;
    uint256 constant IC8y = 1939935864139976487090274419485467179510181254823527802280457426306417534452;
    
    uint256 constant IC9x = 11673649149793377683161157378104745702286045398217216059633601726396628223962;
    uint256 constant IC9y = 936123309773963556795447428787327672195810395738098096444569278153616056684;
    
    uint256 constant IC10x = 5527119554293897391312738749822951732595273008656303406036919772898993757946;
    uint256 constant IC10y = 2618460034739916202748505199843729215411928802994912216099622900755444094867;
    
    uint256 constant IC11x = 170981473698634022454377990928402455977804805176287115842957079236824266815;
    uint256 constant IC11y = 8470805098353926651088146062577482602152017052622991652833829876430058826760;
    
    uint256 constant IC12x = 9493167794200749795186428235183575627108175783278440206927576838224559373770;
    uint256 constant IC12y = 18496334467161376196260811421723544002053934149753276314029717397632771105101;
    
    uint256 constant IC13x = 15377710134131063183844852250093188529384566341210387533923495029118237832551;
    uint256 constant IC13y = 16745870374119619877930424254949787784180945197773804075344213508389552417291;
    
    uint256 constant IC14x = 10645643387661712811373041768128948657015236217168050876299948549361768048585;
    uint256 constant IC14y = 2729834393530084998328042210171853968378017157052261629249946687487130131066;
    
 
    // Memory data
    uint16 constant pVk = 0;
    uint16 constant pPairing = 128;

    uint16 constant pLastMem = 896;

    function verifyProof(uint[2] calldata _pA, uint[2][2] calldata _pB, uint[2] calldata _pC, uint[14] calldata _pubSignals) public view returns (bool) {
        assembly {
            function checkField(v) {
                if iszero(lt(v, r)) {
                    mstore(0, 0)
                    return(0, 0x20)
                }
            }
            
            // G1 function to multiply a G1 value(x,y) to value in an address
            function g1_mulAccC(pR, x, y, s) {
                let success
                let mIn := mload(0x40)
                mstore(mIn, x)
                mstore(add(mIn, 32), y)
                mstore(add(mIn, 64), s)

                success := staticcall(sub(gas(), 2000), 7, mIn, 96, mIn, 64)

                if iszero(success) {
                    mstore(0, 0)
                    return(0, 0x20)
                }

                mstore(add(mIn, 64), mload(pR))
                mstore(add(mIn, 96), mload(add(pR, 32)))

                success := staticcall(sub(gas(), 2000), 6, mIn, 128, pR, 64)

                if iszero(success) {
                    mstore(0, 0)
                    return(0, 0x20)
                }
            }

            function checkPairing(pA, pB, pC, pubSignals, pMem) -> isOk {
                let _pPairing := add(pMem, pPairing)
                let _pVk := add(pMem, pVk)

                mstore(_pVk, IC0x)
                mstore(add(_pVk, 32), IC0y)

                // Compute the linear combination vk_x
                
                g1_mulAccC(_pVk, IC1x, IC1y, calldataload(add(pubSignals, 0)))
                
                g1_mulAccC(_pVk, IC2x, IC2y, calldataload(add(pubSignals, 32)))
                
                g1_mulAccC(_pVk, IC3x, IC3y, calldataload(add(pubSignals, 64)))
                
                g1_mulAccC(_pVk, IC4x, IC4y, calldataload(add(pubSignals, 96)))
                
                g1_mulAccC(_pVk, IC5x, IC5y, calldataload(add(pubSignals, 128)))
                
                g1_mulAccC(_pVk, IC6x, IC6y, calldataload(add(pubSignals, 160)))
                
                g1_mulAccC(_pVk, IC7x, IC7y, calldataload(add(pubSignals, 192)))
                
                g1_mulAccC(_pVk, IC8x, IC8y, calldataload(add(pubSignals, 224)))
                
                g1_mulAccC(_pVk, IC9x, IC9y, calldataload(add(pubSignals, 256)))
                
                g1_mulAccC(_pVk, IC10x, IC10y, calldataload(add(pubSignals, 288)))
                
                g1_mulAccC(_pVk, IC11x, IC11y, calldataload(add(pubSignals, 320)))
                
                g1_mulAccC(_pVk, IC12x, IC12y, calldataload(add(pubSignals, 352)))
                
                g1_mulAccC(_pVk, IC13x, IC13y, calldataload(add(pubSignals, 384)))
                
                g1_mulAccC(_pVk, IC14x, IC14y, calldataload(add(pubSignals, 416)))
                

                // -A
                mstore(_pPairing, calldataload(pA))
                mstore(add(_pPairing, 32), mod(sub(q, calldataload(add(pA, 32))), q))

                // B
                mstore(add(_pPairing, 64), calldataload(pB))
                mstore(add(_pPairing, 96), calldataload(add(pB, 32)))
                mstore(add(_pPairing, 128), calldataload(add(pB, 64)))
                mstore(add(_pPairing, 160), calldataload(add(pB, 96)))

                // alpha1
                mstore(add(_pPairing, 192), alphax)
                mstore(add(_pPairing, 224), alphay)

                // beta2
                mstore(add(_pPairing, 256), betax1)
                mstore(add(_pPairing, 288), betax2)
                mstore(add(_pPairing, 320), betay1)
                mstore(add(_pPairing, 352), betay2)

                // vk_x
                mstore(add(_pPairing, 384), mload(add(pMem, pVk)))
                mstore(add(_pPairing, 416), mload(add(pMem, add(pVk, 32))))


                // gamma2
                mstore(add(_pPairing, 448), gammax1)
                mstore(add(_pPairing, 480), gammax2)
                mstore(add(_pPairing, 512), gammay1)
                mstore(add(_pPairing, 544), gammay2)

                // C
                mstore(add(_pPairing, 576), calldataload(pC))
                mstore(add(_pPairing, 608), calldataload(add(pC, 32)))

                // delta2
                mstore(add(_pPairing, 640), deltax1)
                mstore(add(_pPairing, 672), deltax2)
                mstore(add(_pPairing, 704), deltay1)
                mstore(add(_pPairing, 736), deltay2)


                let success := staticcall(sub(gas(), 2000), 8, _pPairing, 768, _pPairing, 0x20)

                isOk := and(success, mload(_pPairing))
            }

            let pMem := mload(0x40)
            mstore(0x40, add(pMem, pLastMem))

            // Validate that all evaluations ∈ F
            
            checkField(calldataload(add(_pubSignals, 0)))
            
            checkField(calldataload(add(_pubSignals, 32)))
            
            checkField(calldataload(add(_pubSignals, 64)))
            
            checkField(calldataload(add(_pubSignals, 96)))
            
            checkField(calldataload(add(_pubSignals, 128)))
            
            checkField(calldataload(add(_pubSignals, 160)))
            
            checkField(calldataload(add(_pubSignals, 192)))
            
            checkField(calldataload(add(_pubSignals, 224)))
            
            checkField(calldataload(add(_pubSignals, 256)))
            
            checkField(calldataload(add(_pubSignals, 288)))
            
            checkField(calldataload(add(_pubSignals, 320)))
            
            checkField(calldataload(add(_pubSignals, 352)))
            
            checkField(calldataload(add(_pubSignals, 384)))
            
            checkField(calldataload(add(_pubSignals, 416)))
            

            // Validate all evaluations
            let isValid := checkPairing(_pA, _pB, _pC, _pubSignals, pMem)

            mstore(0, isValid)
             return(0, 0x20)
         }
     }
 }
