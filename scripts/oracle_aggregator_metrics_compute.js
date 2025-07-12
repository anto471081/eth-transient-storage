/**
 * Script per l'analisi delle metriche di performance di implementazioni di OracleAggregator
 * 2025
 */
 
const hre = require("hardhat");
const fs = require("fs-extra");
const path = require("path");

async function main() {
  // Parametri di configurazione
  const cliArgs = process.argv.slice(2);
  const ORACLE_COUNT         = parseInt(process.env.ORACLE_COUNT || "50", 10);
  const ITERATIONS           = parseInt(process.env.ITERATIONS   || "10", 10);
  const SC_01 = cliArgs[0] || process.env.SC_01 || "OraMemory";
  const SC_02   = cliArgs[1] || process.env.SC_02   || "OraTransient";
  const SC_TEST = cliArgs[2] || process.env.SC_TEST || "OraTest";
  
  // Directory di output
  const RESULT_DIR = process.env.RESULT_DIR || path.join("results", `${SC_01}_${SC_02}`);
  
  // Prepara la directory di output
  await fs.ensureDir(RESULT_DIR); 

  const OUTPUT_FILE = process.env.OUTPUT_FILE || path.join(RESULT_DIR, "metrics_output.json");

  // Log dei parametri
  console.log(`ORACLE_COUNT=${ORACLE_COUNT}, ITERATIONS=${ITERATIONS}`);
  console.log(`SC_TEST=${SC_TEST}`);
  console.log(`SC_01=${SC_01}`);
  console.log(`SC_02=${SC_02}`);
  console.log(`RESULT_DIR=${RESULT_DIR}`);
  console.log(`OUTPUT_FILE=${OUTPUT_FILE}`);

  // Deploy di N istanze di TestOracle
  const TestOracleFactory = await hre.ethers.getContractFactory(SC_TEST);
  const oracles = [];
  for (let i = 0; i < ORACLE_COUNT; i++) {
    //i * 100 è lo "step" con cui facciamo variare il valore iniziale di ogni oracle
	// aggiungendo 1, otteniamo la sequenza 1, 101, 201, 301
	const oracle = await TestOracleFactory.deploy(i * 100 + 1);
    await oracle.deployed();
    oracles.push(oracle.address);
  }

  // Ottenimento gasPrice e inizializzazione array risultati
  const gasPrice = await hre.ethers.provider.getGasPrice();
  const results = [];

  // Ciclo sui contratti aggregatori da testare
  for (const name of [SC_01, SC_02]) {
    const Factory = await hre.ethers.getContractFactory(name);

    // Misura dimensione bytecode
    const rawBytecode = Factory.bytecode.startsWith("0x")
      ? Factory.bytecode.slice(2)
      : Factory.bytecode;
    const bytecodeSizeBytes = rawBytecode.length / 2;

    // Deploy e metriche di deploy
    const inst = await Factory.deploy();
    await inst.deployed();
    const deployRec = await inst.deployTransaction.wait();
    const deployGas = deployRec.gasUsed.toNumber();
    const deployFeeWei = deployRec.gasUsed.mul(gasPrice).toString();
	
	//Ogni byte è rappresentato da 2 caratteri esadecimali. Dividendo data.length per 2 si ottiene il numero di byte effettivi.
    const deployTxSizeBytes = inst.deployTransaction.data.length / 2;
	
    results.push({
      contract: name,
      action:   "deploy",
      gasUsed:  deployGas,
      gasPrice: gasPrice.toString(),
      feeWei:   deployFeeWei,
      bytecodeSizeBytes,
      txSizeBytes: deployTxSizeBytes
    });

    // Preparazione calldata e misura tx size
    const callData = inst.interface.encodeFunctionData("aggregateQuotes", [oracles]);
    const callDataSize = callData.length / 2;

    console.log(`Benchmark: ${name}.aggregateQuotes() ${ITERATIONS} iterazioni`);
    for (let i = 1; i <= ITERATIONS; i++) {
      const gasUsedBN = await inst.estimateGas.aggregateQuotes(oracles);
      const gasUsed = gasUsedBN.toNumber();
      const feeWei  = gasUsedBN.mul(gasPrice).toString();
      results.push({
        contract:   name,
        action:     "aggregateQuotes",
        iteration:  i,
        gasUsed,
        gasPrice:   gasPrice.toString(),
        feeWei,
        txSizeBytes: callDataSize
      });
    }
  }
  
  // Esportazione delle metriche in un unico file
  await fs.writeJson(OUTPUT_FILE, results, { spaces: 2 });
  console.log(`File completo scritto in: ${OUTPUT_FILE}`);
  
}

// Esecuzione main e gestione errori
main().catch(e => { console.error(e); process.exit(1); });