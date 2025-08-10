const contractAddress = "0x45f51f220f3579E7db2A0F088aDabf1Ae7916491";
const contractABI = [ /* ABI SAME AS YOURS */ 
	{
		"anonymous": false,
		"inputs": [
			{ "indexed": true, "internalType": "uint256", "name": "id", "type": "uint256" },
			{ "indexed": true, "internalType": "address", "name": "owner", "type": "address" },
			{ "indexed": false, "internalType": "string", "name": "name", "type": "string" }
		],
		"name": "ItemRegistered",
		"type": "event"
	},
	{
		"anonymous": false,
		"inputs": [
			{ "indexed": true, "internalType": "uint256", "name": "id", "type": "uint256" },
			{ "indexed": true, "internalType": "address", "name": "from", "type": "address" },
			{ "indexed": true, "internalType": "address", "name": "to", "type": "address" }
		],
		"name": "OwnershipTransferred",
		"type": "event"
	},
	{
		"inputs": [{ "internalType": "string", "name": "name", "type": "string" }],
		"name": "registerItem",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [
			{ "internalType": "uint256", "name": "id", "type": "uint256" },
			{ "internalType": "address", "name": "newOwner", "type": "address" }
		],
		"name": "transferOwnership",
		"outputs": [],
		"stateMutability": "nonpayable",
		"type": "function"
	},
	{
		"inputs": [],
		"name": "itemCount",
		"outputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
		"stateMutability": "view",
		"type": "function"
	},
	{
		"inputs": [{ "internalType": "uint256", "name": "", "type": "uint256" }],
		"name": "items",
		"outputs": [
			{ "internalType": "uint256", "name": "id", "type": "uint256" },
			{ "internalType": "string", "name": "name", "type": "string" },
			{ "internalType": "address", "name": "owner", "type": "address" }
		],
		"stateMutability": "view",
		"type": "function"
	}
];

let provider, signer, contract, account;

// ✅ Initialize Contract
async function initContract() {
    if (typeof ethers === "undefined") return alert("❌ Ethers.js not loaded!");
    if (!window.ethereum) return alert("❌ MetaMask not detected!");

    try {
        provider = new ethers.providers.Web3Provider(window.ethereum);
        signer = provider.getSigner();
        contract = new ethers.Contract(contractAddress, contractABI, signer);
        console.log(`✅ Contract ready: ${contractAddress}`);
    } catch (err) {
        console.error("❌ Contract init failed:", err);
        alert("Contract init error");
    }
}

// ✅ Connect Wallet
document.getElementById("connectButton").addEventListener("click", async () => {
    if (!window.ethereum) return alert("MetaMask not detected!");

    try {
        const accounts = await ethereum.request({ method: "eth_requestAccounts" });
        account = accounts[0];
        document.getElementById("connectButton").innerText =
            `Connected: ${account.slice(0, 6)}...${account.slice(-4)}`;
        console.log("🔗 Connected:", account);
        await initContract();
    } catch (err) {
        console.error("❌ Wallet connection failed:", err);
    }
});

// ✅ Register Item
document.getElementById("registerButton").addEventListener("click", async () => {
    if (!contract) return alert("Connect wallet first!");
    const itemName = document.getElementById("itemName").value.trim();
    if (!itemName) return alert("Enter an item name");

    try {
        console.log(`📦 registerItem("${itemName}")...`);
        const tx = await contract.registerItem(itemName);
        console.log("⏳ Waiting for confirmation...");
        await tx.wait();
        console.log(`✅ Registered: ${itemName}`);
        alert(`Item registered: ${itemName}`);
        document.getElementById("itemName").value = ""; // Clear input
    } catch (err) {
        console.error("❌ Register failed:", err);
        alert(`Register failed: ${err.message}`);
    }
});

// ✅ Transfer Ownership
document.getElementById("transferButton").addEventListener("click", async () => {
    if (!contract) return alert("Connect wallet first!");
    const id = document.getElementById("itemId").value;
    const newOwner = document.getElementById("newOwner").value.trim();
    if (!id || !newOwner) return alert("Enter both ID & new owner");

    try {
        console.log(`📦 transferOwnership(${id}, ${newOwner})...`);
        const tx = await contract.transferOwnership(id, newOwner);
        console.log("⏳ Waiting for confirmation...");
        await tx.wait();
        console.log(`✅ Ownership transferred!`);
        alert("Ownership transferred!");
        document.getElementById("itemId").value = "";
        document.getElementById("newOwner").value = "";
    } catch (err) {
        console.error("❌ Transfer failed:", err);
        alert(`Transfer failed: ${err.message}`);
    }
});
