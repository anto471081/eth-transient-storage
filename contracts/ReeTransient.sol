// SPDX-License-Identifier: MIT
pragma solidity ^0.8.28;

/**
 * @title Reentrancy Lock tramite Transient Storage
 * @notice Protegge la funzione `claimReward` da attacchi di reentrancy sfruttando la memoria transitoria (EIP-1153)
 * @dev Il modifier `nonReentrantTransient` utilizza gli opcode `TSTORE`/`TLOAD` per impostare un lock volatile
 * all’ingresso e rilasciarlo al termine della funzione, senza alcuna scrittura permanente in storage.
 * 2025
 */
contract ReeTransient {
    /// @dev Emesso quando la ricompensa viene reclamata con successo
    event GiftClaimedTransient(address indexed caller);

    /**
     * @dev Modifier che impedisce la reentrancy usando transient storage:
     *      all’ingresso calcola una chiave univoca in memoria, verifica con `tload` che non sia già impostata,
     *      imposta il lock con `tstore`, esegue la funzione e infine rilascia il lock con un secondo `tstore`.
     *      In caso di tentativo di reentrancy, esegue un `revert` immediato.
     */
    modifier nonReentrantTransient() {
        assembly {
            // carica 32 byte a zero in memory per il calcolo della chiave
            mstore(0x00, 0)
            let key := keccak256(0x00, 0x20)
            // se il lock è già attivo, revert istantaneo
            if tload(key) { revert(0, 0) }
            // acquisisci il lock (tstore = 1)
            tstore(key, 1)
        }
        _; // esegue la funzione protetta
        assembly {
		    mstore(0x00, 0)
			let key := keccak256(0x00, 0x20)
            // rilascia il lock (tstore = 0)
            tstore(key, 0)
        }
    }

    /**
     * @notice Reclama la ricompensa protetta dal reentrancy guard
     * @dev Applica `nonReentrantTransient` per impedire reentrancy, chiama `_inner()` per misurare
     * l’overhead e, in caso di successo, emette `GiftClaimedTransient`; altrimenti revert.
     */
    function claimReward() external nonReentrantTransient {
        bool success;
        // esegue una chiamata interna isolata per misurare il sovraccarico del guard
        try this._inner() {
            success = true;
        } catch {
            success = false;
        }
        if (success) {
            emit GiftClaimedTransient(msg.sender);
        } else {
            revert("TransientLock: inner fallita");
        }
    }

    /**
     * @notice Funzione pura usata per isolare e misurare l’overhead di chiamata
     * @dev Non altera alcuno stato, serve esclusivamente a generare una transazione on-chain
     */
    function _inner() external pure {
        // nessuna operazione
    }
}
