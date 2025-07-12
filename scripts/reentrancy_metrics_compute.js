/**
 * Script per l'analisi delle metriche di performance di implementazioni di protezione contro la reentrancy
 * 2025
 */

const hre = require("hardhat");
const fs = require("fs-extra");
const path = require("path");

async function main() {
  // Parametri di configurazione
  const cliArgs = process.argv.slice(2);
  const ITERATIONS = parseInt(process.env.ITERATIONS || cliArgs[0] || "5000", 10);
  const SC_01 = process.env.SC_01 || cliArgs[1] || "ReeStorage";
  const SC_02 = process.env.SC_02 || cliArgs[2] || "ReeTransient";

  // Directory di output
  const RESULT_DIR = process.env.RESULT_DIR || path.join("results", `${SC_01}_${SC_02}`);
  
  // Prepara la directory di output
  await fs.ensureDir(RESULT_DIR);
  
  const OUTPUT_FILE = process.env.OUTPUT_FILE || path.join(RESULT_DIR, "metrics_output.json");

  // Log dei parametri
  console.log(`ITERATIONS=${ITERATIONS}`);
  console.log(`SC_01=${SC_01}`);
  console.log(`SC_02=${SC_02}`);
  console.log(`RESULT_DIR=${RESULT_DIR}`);
  console.log(`OUTPUT_FILE=${OUTPUT_FILE}`);

  // Preleva il gasPrice corrente dal provider Hardhat
  const gasPrice = await hre.ethers.provider.getGasPrice();
  console.log(`Gas price fissato a ${gasPrice.toString()} Wei`);

  // Array per raccogliere tutte le misurazioni
  const results = [];

  // Ciclo di test sui contratti
  for (const name of [SC_01, SC_02]) {
    console.log(`### Test per contratto: ${name} ###`);

    // Ottieni factory e misura dimensione bytecode
    const Factory = await hre.ethers.getContractFactory(name);
    const rawBytecode = Factory.bytecode.startsWith("0x") ? Factory.bytecode.slice(2) : Factory.bytecode;
    const bytecodeSizeBytes = rawBytecode.length / 2;
    console.log(`Bytecode size: ${bytecodeSizeBytes} bytes`);

    // Effettua il deploy del contratto e misura gas/fee/tx size
    console.log(`Deploy in corso...`);
    const instance = await Factory.deploy();
    await instance.deployed();
    const deployRec = await instance.deployTransaction.wait();
    const deployGas = deployRec.gasUsed.toNumber();
    const deployFeeWei = deployRec.gasUsed.mul(gasPrice);
    const deployTxSizeBytes = instance.deployTransaction.data.length / 2;
    console.log(`Deploy gasUsed: ${deployGas}, fee: ${deployFeeWei.toString()} Wei, tx size: ${deployTxSizeBytes} bytes`);

    results.push({
      contract: name,
      action: "deploy",
      gasUsed: deployGas,
      gasPrice: gasPrice.toString(),
      feeWei: deployFeeWei.toString(),
      bytecodeSizeBytes,
      txSizeBytes: deployTxSizeBytes
    });

    // Ciclo di chiamate a claimReward per misurare costi ripetuti
    console.log(`Inizio ciclo di ${ITERATIONS} chiamate a claimReward()`);
    for (let i = 1; i <= ITERATIONS; i++) {
      try {
        const tx = await instance.claimReward({ gasPrice });
        const rec = await tx.wait();
        const gasUsed = rec.gasUsed.toNumber();
        const feeWei = rec.gasUsed.mul(gasPrice);
        const txSizeBytes = tx.data.length / 2;
        results.push({
          contract: name,
          action: "claimReward",
          iteration: i,
          gasUsed,
          gasPrice: gasPrice.toString(),
          feeWei: feeWei.toString(),
          txSizeBytes
        });
		// Se l’iterazione è multipla di 1000, logga il progresso
        if (i % 1000 === 0) console.log(`Iterazione ${i} completata`);
      } catch (error) {
        console.error(`Errore all'iterazione ${i}:`, error.message || error);
      }
    }
  }

  // Scrive tutte le metriche in formato JSON su OUTPUT_FILE
  await fs.writeJson(OUTPUT_FILE, results, { spaces: 2 });
  console.log(`File completo scritto in: ${OUTPUT_FILE}`);


}

// Esecuzione dello script e gestione degli errori globali
main().catch((err) => {
  console.error(`Errore critico:`, err.message || err);
  process.exit(1);
});
