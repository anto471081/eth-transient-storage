// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IOraTest {
    function fetchPrice() external view returns (uint256);
}

/**
 * @title Oracle Aggregator Transient Storage
 * @notice Interroga sequenzialmente gli oracoli e ne restituisce la media dei prezzi,
 *         sfruttando il transient storage in modo sicuro.
 * @dev    Utilizza TSTORE/TLOAD per memorizzare temporaneamente i prezzi e li pulisce
 *         sia in ingresso sia in uscita per evitare side-effects tra chiamate.
 * 2025
 */
contract OraTransient {
    /**
     * @notice Calcola la media dei prezzi restituiti dagli oracoli
     * @param oracles Array di indirizzi degli oracoli
     * @return avgPrice Prezzo medio calcolato
     * @dev    1) Pulizia iniziale degli slot transient  
     *         2) Scrittura e lettura in un unico blocco assembly per sommare
     *         3) Calcolo media  
     *         4) Pulizia finale degli slot transient
     */
    function aggregateQuotes(address[] memory oracles) external returns (uint256 avgPrice) {
        uint256 len = oracles.length;
        require(len > 0, "Nessun oracolo presente");

        _cleanup(len);

        uint256 sum = 0;
        for (uint256 i = 0; i < len; ++i) {
            uint256 price = IOraTest(oracles[i]).fetchPrice();
            assembly {
				tstore(i, price)
                let p := tload(i)
                sum := add(sum, p)
            }
        }

        avgPrice = sum / len;
    }

    /**
     * @dev Pulisce gli slot [0..slots) dallo transient storage
     */
    function _cleanup(uint256 slots) internal {
        for (uint256 i = 0; i < slots; ++i) {
            assembly { tstore(i, 0) }
        }
    }
}
