// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title Oracle Aggregator Test
 * @notice Smarr Contract di esempio che espone un prezzo fisso per scopi di test
 * @dev    Usato negli script di test per restituire sempre lo stesso valore
 * 2025
 */
contract OraTest {
    uint256 private immutable price;

    /**
     * @notice Inizializza l’oracolo con un prezzo
     * @param _price Valore di prezzo da restituire
     */
    constructor(uint256 _price) {
        price = _price;
    }

    /**
     * @notice Restituisce il prezzo memorizzato nell’oracolo
     * @return Prezzo impostato in fase di deploy
     */
    function fetchPrice() external view returns (uint256) {
        return price;
    }
}
