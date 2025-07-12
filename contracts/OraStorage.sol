// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IOraTest {
    function fetchPrice() external view returns (uint256);
}

/**
 * @title Oracle Aggregator Persistent Storage
 * @notice Interroga sequenzialmente gli oracoli e ne restituisce la media dei prezzi,
 *         usando lo storage permanente (SSTORE/SLOAD).
 * @dev    Salva i prezzi in un mapping di storage e lo pulisce al termine di ogni chiamata.
 * 2025
 */
contract OraStorage {
    /// @dev Storage permanente per i prezzi temporanei
    mapping(uint256 => uint256) private _prices;

    /**
     * @notice Calcola la media dei prezzi restituiti dagli oracoli
     * @param oracles Array di indirizzi degli oracoli
     * @return avgPrice Prezzo medio calcolato
     * @dev    1) fetchPrice()
     *         2) store + sum
     *         3) delete
     */
    function aggregateQuotes(address[] memory oracles) external returns (uint256 avgPrice) {
        uint256 len = oracles.length;
        require(len > 0, "Nessun oracolo presente");

        uint256 sum = 0;
        
        //Scrittura a lettura su Storage permanente
		for (uint256 i = 0; i < len; ++i) {
			// SSTORE: salva temporaneamente i prezzi
            uint256 price = IOraTest(oracles[i]).fetchPrice();
            _prices[i] = price;
			// SLOAD: legge e somma
			sum += _prices[i];
        }

        // Calcola media
        avgPrice = sum / len;

        // Cleanup: cancella lo storage
        for (uint256 i = 0; i < len; ++i) {
            delete _prices[i];
        }
    }
}
