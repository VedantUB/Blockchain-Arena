# P2P Cryptocurrency Network Simulator

This project implements a discrete-event simulator of a Peer-to-Peer (P2P) cryptocurrency network, modeling realistic transaction propagation, mining, and blockchain growth based on the Proof-of-Work consensus protocol.

## Files

- `simulator.py`: Main simulation script. Generates blockchain data and prints statistics.
- `tree_visualisation.py`: Visualization tool to analyze the blockchain tree and peer mining performance.
- `blockchain_data.json`: Output from simulator (generated after simulation run).
- `Figure_1.png`: Tree structure of the blockchain.
- `Figure_2.png`: Mining stats image representation.

## Running the Simulator

```bash
python simulator.py --n 20 --z0 40 --z1 40 --ttx 1.0 --I 600 --sim-time 3000 --output blockchain_data.json