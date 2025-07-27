Esperimenti su transient storage in Solidity: misurazione di gas e dimensione di transazione

Licenza: MIT

===  Struttura del progetto

/
├─ contracts/             
│  ├─ OraMemory.sol       
│  ├─ OraStorage.sol       
│  ├─ OraTransient.sol     
│  ├─ ReeStorage.sol       
│  └─ ReeTransient.sol     
├─ scripts/                
│  ├─ oracle_aggregator_metrics_compute.js  
│  ├─ oracle_aggregator_metrics_plot.py     
│  ├─ reentrancy_metrics_compute.js         
│  └─ reentrancy_metrics_plot.py            
├─ results/                   
├─ package.json            
├─ requirements.txt        
├─ hardhat.config.js       
├─ .gitignore              
└─ LICENSE               
└─ README.md               

=== Setup

Clona il repository

git clone https://github.com/anto471081/eth-transient-storage.git

===  Configura l'ambiente Python

python3 -m venv venv

source venv/bin/activate

pip install -r requirements.txt

=== Installa dipendenze Node.js

npm install

=== Compila i contratti

npx hardhat compile

=== Scripts disponibili

npx hardhat compile

npx hardhat run scripts/oracle_aggregator_metrics_compute.js

npx hardhat run scripts/reentrancy_metrics_compute.js

<input file> python3 scripts/reentrancy_metrics_plot.py

<input file> python3 scripts/oracle_aggregator_metrics_plot.py

=== Esempi di esecuzione reale degli script coi parametri (reentrancy)

ITERATIONS=5000 SC_01=ReeStorage SC_02=ReeTransient npx hardhat run scripts/reentrancy_metrics_compute.js

METRICS_JSON=results/ReeStorage_ReeTransient/metrics_output.json python3 scripts/reentrancy_metrics_plot.py

=== Esempi di esecuzione reale degli script coi parametri (oracle)

ORACLE_COUNT=50 ITERATIONS=10 SC_TEST=OraTest SC_01=OraMemory SC_02=OraTransient npx hardhat run scripts/oracle_aggregator_metrics_compute.js

ORACLE_COUNT=50 ITERATIONS=10 SC_TEST=OraTest SC_01=OraStorage SC_02=OraTransient npx hardhat run scripts/oracle_aggregator_metrics_compute.js

METRICS_JSON=results/OraMemory_OraTransient/metrics_output.json python3 scripts/oracle_aggregator_metrics_plot.py

METRICS_JSON=results/OraStorage_OraTransient/metrics_output.json python3 scripts/oracle_aggregator_metrics_plot.py
