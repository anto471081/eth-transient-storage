// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IOraTest {
    function fetchPrice() external view returns (uint256);
}

/**
 * @title Oracle Aggregator TransientNA (Not Assembly)
 * @notice Aggrega prezzi da più oracoli esterni utilizzando transient storage senza l'utilizzo diretto degli OPCODE TLOAD/TSTORE ma con variabili definite transient in Solidity
 * @dev Itera su `oracles`, chiama fetchPrice(), somma e calcola la media.
 * 2025
 */
contract OraTransientNA {

	uint256 transient sumTransient; 	// somma dei prezzi degli oracoli
	
    /**
     * @notice Calcola la media dei prezzi restituiti dagli oracoli
     * @param oracles Array di indirizzi degli oracoli da interrogare
     * @return avgPrice Prezzo medio calcolato
     * @dev    Il metodo itera sull'array chiamando fetchPrice() su ciascun
     *         oracle e sommando i prezzi, quindi divide la somma per il numero di oracoli.
     */
    function aggregateQuotes(address[] memory oracles)
        external
        returns (uint256 avgPrice)
    {
		uint256 len = oracles.length;
        require(len > 0, "Nessun oracolo presente");
		sumTransient = 0; 											//scrittura in transient storage
        for (uint256 i = 0; i < len; ++i) {
            sumTransient += IOraTest(oracles[i]).fetchPrice();								//lettura e scrittura su transient storage
        }

        avgPrice = sumTransient / len;								//lettura da transient storage
    }
}
