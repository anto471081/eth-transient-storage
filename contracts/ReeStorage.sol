// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title Reentrancy Lock tramite Storage Permanente
 * @notice Protegge la funzione `claimReward` da attacchi di reentrancy utilizzando una variabile in storage
 * @dev Impiega `SSTORE`/`SLOAD` per settare e resettare un flag booleano; le funzioni protette devono usare il modifier `nonReentrant`
 * 2025
 */
contract ReeStorage {
    /**
     * @dev Emesso quando la funzione protetta termina con successo e la ricompensa viene reclamata
     * @param caller Indirizzo che ha invocato con successo `claimReward`
     */
    event RewardClaimed(address indexed caller);

    /// @dev Flag booleano in storage che indica se il contratto è in esecuzione protetta
    bool private locked;

    /**
     * @notice Modifier che impedisce chiamate ricorsive non autorizzate
     * @dev 
     * 1) Verifica con `SLOAD` che `locked` sia `false`; in caso contrario reverta con messaggio  
     * 2) Imposta `locked = true` con `SSTORE` prima di eseguire la funzione  
     * 3) Al termine dell’esecuzione, ripristina `locked = false`  
     */
    modifier nonReentrant() {
        // 1) Se il lock è già attivo, blocca l’esecuzione
        require(!locked, "StorageLock: reentrant");
        // 2) Attiva il lock
        locked = true;
        // 3) Esegue la funzione protetta
        _;
        // 4) Disattiva il lock
        locked = false;
    }

    /**
     * @notice Reclama una ricompensa, protetto dal modifier `nonReentrant`
     * @dev 
     * 1) Effettua una chiamata esterna a `_inner` per misurare l’overhead  
     * 2) Se la chiamata ha successo, emette `RewardClaimed`; in caso contrario revert con messaggio  
     */
    function claimReward() external nonReentrant {
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
            revert("StorageLock: inner fallita");
        }
    }

    /**
     * @notice Funzione interna pura usata per misurare l’overhead di chiamata
     * @dev Non modifica alcuno stato; serve solo a generare una transazione on-chain
     */
    function _inner() external pure {
        // nessuna operazione
    }
}
