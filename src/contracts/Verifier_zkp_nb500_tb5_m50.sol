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
    uint256 constant alphax  = 6880372625406566257793153631937220348785006390954043587403204934670086827149;
    uint256 constant alphay  = 5652650615377136738606562338968695585379640084393605471847147598914335748648;
    uint256 constant betax1  = 17543808932212240650649354414873180275785829022073254230571365961920607507404;
    uint256 constant betax2  = 8689139287122496822811155794342268577299432160338426636028863041343484043322;
    uint256 constant betay1  = 12653761602355128462270518204028145496887873158756233259230126881480422052067;
    uint256 constant betay2  = 10979586394400302422871000159705349339447189274179201816121759750651317031639;
    uint256 constant gammax1 = 11559732032986387107991004021392285783925812861821192530917403151452391805634;
    uint256 constant gammax2 = 10857046999023057135944570762232829481370756359578518086990519993285655852781;
    uint256 constant gammay1 = 4082367875863433681332203403145435568316851327593401208105741076214120093531;
    uint256 constant gammay2 = 8495653923123431417604973247489272438418190587263600148770280649306958101930;
    uint256 constant deltax1 = 13950891549699890608875327939267909922639768856915739223107040486410452338178;
    uint256 constant deltax2 = 9464265069401352954024294476582955054597089643798421397377800614771754079138;
    uint256 constant deltay1 = 16339484545086607015470943142486218485683952370503005438987279914382795022988;
    uint256 constant deltay2 = 18619330825217917648520123585157549888917117027267101948609752239291603392141;

    
    uint256 constant IC0x = 15950683730114728051805856896754759897849252657602136919554289925002339717674;
    uint256 constant IC0y = 5317449940325479145205353828579991128141109416511446388432203191486091048524;
    
    uint256 constant IC1x = 17891443427698426627342353808862730648378352834133391610046207714109756643663;
    uint256 constant IC1y = 17401954470434988576657918463786424157301106163978676914815520282095180236133;
    
    uint256 constant IC2x = 5042925700859285819472258334980097278181003892554071550381435431690671445289;
    uint256 constant IC2y = 8198885791019578975486464012651592315697814530520624265124060638903073497747;
    
    uint256 constant IC3x = 6886090875686769294030952738225361803533106291944072819498657088894487321329;
    uint256 constant IC3y = 380736641331654355866505012206500235631736811878606255173811007266043736748;
    
    uint256 constant IC4x = 11232251844033725230329419077385151456658546416139696428253603007233204185936;
    uint256 constant IC4y = 11044983197760810299699156367713833858302134635016247551124937230401223985476;
    
    uint256 constant IC5x = 16682900328426201745177785510024540106716715532252904632012674254691253635511;
    uint256 constant IC5y = 9803162452587406349979398541575168569422140322719380653483880119203199142845;
    
    uint256 constant IC6x = 2938525133280656115060200031851670160559893190537142110044043246927491009043;
    uint256 constant IC6y = 4245430570641321173224893893549836737727859480269496212707165252113703655418;
    
    uint256 constant IC7x = 10984301189467056207373380515088073093433616703988993730300549781784819142068;
    uint256 constant IC7y = 17783516606032306732286094121587046908136760646264612714092983437902863023727;
    
    uint256 constant IC8x = 21749951716782722028418385470646119107806856544145008552637083712771781428892;
    uint256 constant IC8y = 12517072270438229438782935875560290513570533364083159033899894610214342284503;
    
    uint256 constant IC9x = 5076201113519506947861180692608982901245018595295202201670514221865020956991;
    uint256 constant IC9y = 11922734967423555255865159465244285625258948184614164263793351178680237349507;
    
    uint256 constant IC10x = 10983772703532766001742337086822206750262040480778974140857680371670193533928;
    uint256 constant IC10y = 851763339929129991758187146464159057337889465456441153999643268217587930307;
    
    uint256 constant IC11x = 6969088148854126678151125933277136894933775144250409152632066402994698746337;
    uint256 constant IC11y = 14341038957174749606997614377042401177279265063316033935140060848375698972876;
    
    uint256 constant IC12x = 11206246894715073225204329147343284616080528011869674938412689742050942647455;
    uint256 constant IC12y = 2548482707121198736287925382498231942231025019391022455132729227884182795168;
    
    uint256 constant IC13x = 6931225900883050401420781395517465734929877657768629635024332523939780444796;
    uint256 constant IC13y = 16584165323844285121363053737004127165876220545158599798580944760247539134973;
    
    uint256 constant IC14x = 3565181881775453661312645831516510409365886834106163899218796942024691833857;
    uint256 constant IC14y = 16419029812589595604338362021655889677191664213367670387881231335988032546051;
    
 
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
