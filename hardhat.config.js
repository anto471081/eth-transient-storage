require("@nomiclabs/hardhat-ethers");
require("hardhat-tracer");
module.exports = {
  solidity: {
    version: "0.8.28",
    settings: { optimizer: { enabled: true, runs: 200 }, evmVersion: "cancun" }
  },
  networks: {
    hardhat: { hardfork: "cancun", initialBaseFeePerGas:0, blockGasLimit:15_000_000, allowUnlimitedContractSize:true }
  }
};

