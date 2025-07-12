// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

interface IOraTest {
    function fetchPrice() external view returns (uint256);
}

/**
 * @title Oracle Aggregator Memory
 * @notice Aggrega prezzi da più oracoli esterni utilizzando un buffer in memoria.
 * @dev  Itera su `oracles`, chiama fetchPrice(), somma e calcola la media.
 * 2025
 */
contract OraMemory {
    /**
     * @notice Calcola la media dei prezzi restituiti dagli oracoli
     * @param oracles Array di indirizzi degli oracoli da interrogare
     * @return avgPrice Prezzo medio calcolato
     * @dev    Il metodo itera sull'array in memoria, chiamando fetchPrice() su ciascun
     *         oracle e sommando i prezzi, quindi divide la somma per il numero di oracoli.
     */
    function aggregateQuotes(address[] memory oracles)
        external
        view
        returns (uint256 avgPrice)
    {
        uint256 len = oracles.length;
        require(len > 0, "Nessun oracolo presente");

        uint256 sum = 0;
        for (uint256 i = 0; i < len; ++i) {
            uint256 price = IOraTest(oracles[i]).fetchPrice();
            sum += price;
        }

        avgPrice = sum / len;
    }
}
