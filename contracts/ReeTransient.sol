// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title Protezione da Reentrancy con variabile memorizzata in transient storage
 * @notice Protegge da Reentrancy usando `bool transient locked` come flag temporanea salvata su transient storage
 * @dev Le funzioni protette devono usare il modifier `nonReentrantTransient`
 * 2025
 */
contract ReeTransient {
    /**
     * @dev Emesso quando la funzione protetta termina con successo e la ricompensa viene reclamata
     * @param caller Indirizzo che ha invocato con successo `claimReward`
     */
    event RewardClaimed(address indexed caller);

    /// @dev Flag salvato transient storage, esiste solo durente la transazione. Indica se lo Smart Contract è in esecuzione protetta
    bool transient locked;

    /**
     * @dev Modifier che protegge da attacchi di reentrancy usando transient storage
     * 
     * Utilizza la variabile `bool transient locked`, che viene memorizzata in transient storage
     * 
     * Controlla che `locked` sia `false`, altrimenti revert
     * Imposta `locked = true` per bloccare ulteriori chiamate durante l’esecuzione
     * Esegue la funzione claimReward() protetta
     * Rilascia il locked impostando `locked = false`.
     * 
     */
    modifier nonReentrantTransient() {
        // 1) Se il lock è già attivo, blocca l’esecuzione
        require(!locked, "Transientlocked: Reentrancy");
        // 2) Attiva il lock
        locked = true;
        // 3) Esegue la funzione protetta
        _;
        // 4) Disattiva il lock
        locked = false;		
    }

    /**
     * @notice Reclama una ricompensa, protetto dal modifier `nonReentrantTransient`
     * @dev 
     * 1) Effettua una chiamata esterna a `_inner`  
     * 2) Se la chiamata ha successo, emette `RewardClaimed`; in caso contrario revert con messaggio  
     */
    function claimReward() external nonReentrantTransient {
        bool success;
        // Chiamata esterna isolata per misurare il sovraccarico del lock
        try this._inner() {
            success = true;
        } catch {
            success = false;
        }
        // Se l’operazione interna ha avuto esito positivo, emetto evento
        if (success) {
            emit RewardClaimed(msg.sender);
        } else {
            // In caso di fallimento, revert con messaggio descrittivo
            revert("Transientlocked: inner fallita");
        }
    }

    /**
     * @notice Funzione espediente per distinguere il costo “puro” del meccanismo di protezione dalla logica effettiva della funzione claimReward() 
     * @dev Esegue un CALL esterno, simulando un funzionamento in contesto reale 
     */
    function _inner() external pure {
        // nessuna operazione
    }
}