import heapq
import random
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import json
import argparse
from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Set, Optional, Tuple
import uuid
from collections import defaultdict, deque
import time

class EventType(Enum):
    GENERATE_TRANSACTION = "generate_transaction"
    RECEIVE_TRANSACTION = "receive_transaction"
    GENERATE_BLOCK = "generate_block"
    RECEIVE_BLOCK = "receive_block"
    START_MINING = "start_mining"

@dataclass
class Event:
    time: float
    event_type: EventType
    node_id: int
    data: dict
    
    def __lt__(self, other):
        return self.time < other.time

@dataclass
class Transaction:
    txn_id: str
    sender_id: int
    receiver_id: int
    amount: float
    size: int = 1024  # 1KB in bits
    
    def __str__(self):
        return f"TxnID: {self.txn_id} ID{self.sender_id} pays ID{self.receiver_id} {self.amount} coins"

@dataclass
class Block:
    block_id: str
    prev_block_id: str
    transactions: List[Transaction]
    miner_id: int
    timestamp: float
    size: int
    
    def __post_init__(self):
        # Calculate block size (1KB base + transaction sizes)
        self.size = 1024 + sum(tx.size for tx in self.transactions)  # in bits
    
    def is_valid_size(self):
        return self.size <= 8 * 10**6  # 1MB = 8 * 10^6 bits

class Peer:
    def __init__(self, peer_id: int, is_slow: bool, is_low_cpu: bool):
        self.peer_id = peer_id
        self.is_slow = is_slow
        self.is_low_cpu = is_low_cpu
        self.balance = 1000.0  # Initial balance
        self.connected_peers: Set[int] = set()
        self.pending_transactions: List[Transaction] = []
        self.blockchain_tree = BlockchainTree()
        self.seen_transactions: Set[str] = set()
        self.seen_blocks: Set[str] = set()
        self.mining_event_id: Optional[str] = None
        
        # Hash power calculation
        base_hash_power = 1.0 if self.is_low_cpu else 10.0
        self.hash_power = base_hash_power
        
    def add_peer(self, peer_id: int):
        self.connected_peers.add(peer_id)
    
    def get_balance(self, txn_history: List[Transaction]) -> float:
        """Calculate current balance based on transaction history"""
        balance = 1000.0  # Initial balance
        for tx in txn_history:
            if tx.sender_id == self.peer_id:
                balance -= tx.amount
            elif tx.receiver_id == self.peer_id:
                balance += tx.amount
        return balance

class BlockchainTree:
    def __init__(self):
        self.blocks: Dict[str, Block] = {}
        self.children: Dict[str, List[str]] = defaultdict(list)
        self.parent: Dict[str, str] = {}
        self.block_arrival_times: Dict[str, float] = {}
        self.genesis_id = "genesis"
        self.longest_chain_tip = self.genesis_id
        
        # Create genesis block
        genesis_block = Block(
            block_id=self.genesis_id,
            prev_block_id="",
            transactions=[],
            miner_id=-1,
            timestamp=0.0,
            size=1024
        )
        self.blocks[self.genesis_id] = genesis_block
        self.block_arrival_times[self.genesis_id] = 0.0
    
    def add_block(self, block: Block, arrival_time: float) -> bool:
        """Add block to tree and return True if it extends the longest chain"""
        if block.block_id in self.blocks:
            return False
            
        # Validate parent exists
        if block.prev_block_id not in self.blocks:
            return False
            
        self.blocks[block.block_id] = block
        self.parent[block.block_id] = block.prev_block_id
        self.children[block.prev_block_id].append(block.block_id)
        self.block_arrival_times[block.block_id] = arrival_time
        
        # Check if this creates a new longest chain
        if self.get_chain_length(block.block_id) > self.get_chain_length(self.longest_chain_tip):
            self.longest_chain_tip = block.block_id
            return True
        
        return False
    
    def get_chain_length(self, block_id: str) -> int:
        """Get length of chain ending at block_id"""
        length = 0
        current = block_id
        while current != "":
            length += 1
            current = self.parent.get(current, "")
        return length
    
    def get_longest_chain(self) -> List[str]:
        """Get the longest chain as list of block IDs"""
        chain = []
        current = self.longest_chain_tip
        while current != "":
            chain.append(current)
            current = self.parent.get(current, "")
        return list(reversed(chain))
    
    def get_transactions_in_longest_chain(self) -> List[Transaction]:
        """Get all transactions in the longest chain"""
        transactions = []
        for block_id in self.get_longest_chain():
            if block_id != self.genesis_id:
                transactions.extend(self.blocks[block_id].transactions)
        return transactions

class Network:
    def __init__(self, n_peers: int):
        self.n_peers = n_peers
        self.graph = nx.Graph()
        self.latencies: Dict[Tuple[int, int], Dict[str, float]] = {}
        
        # Add nodes
        for i in range(n_peers):
            self.graph.add_node(i)
        
        self._create_connected_topology()
        self._calculate_latencies()
    
    def _create_connected_topology(self):
        """Create a connected P2P network where each node has 3-6 connections"""
        # Ensure connectivity by creating a spanning tree first
        nodes = list(range(self.n_peers))
        random.shuffle(nodes)
        
        for i in range(len(nodes) - 1):
            self.graph.add_edge(nodes[i], nodes[i + 1])
        
        # Add additional random edges to reach 3-6 degree per node
        for node in range(self.n_peers):
            current_degree = self.graph.degree[node]
            target_degree = random.randint(max(3, current_degree), 6)
            
            attempts = 0
            while current_degree < target_degree and attempts < 50:
                neighbor = random.randint(0, self.n_peers - 1)
                if neighbor != node and not self.graph.has_edge(node, neighbor):
                    self.graph.add_edge(node, neighbor)
                    current_degree += 1
                attempts += 1
    
    def _calculate_latencies(self):
        """Pre-calculate latency parameters for all connections"""
        for edge in self.graph.edges():
            i, j = edge
            rho = random.uniform(0.01, 0.5)  # 10ms to 500ms
            self.latencies[(i, j)] = {'rho': rho}
            self.latencies[(j, i)] = {'rho': rho}  # Symmetric
    
    def get_latency(self, sender_id: int, receiver_id: int, message_size_bits: int, 
                   sender_slow: bool, receiver_slow: bool) -> float:
        """Calculate message latency between two nodes"""
        if not self.graph.has_edge(sender_id, receiver_id):
            return float('inf')
        
        params = self.latencies[(sender_id, receiver_id)]
        rho = params['rho']
        
        # Link speed: 100 Mbps if both fast, 5 Mbps if either is slow
        c = 5e6 if (sender_slow or receiver_slow) else 100e6  # bits per second
        
        # Queuing delay: exponential with mean 96kb/c
        d = np.random.exponential(96000 / c)
        
        return rho + message_size_bits / c + d
    
    def get_neighbors(self, node_id: int) -> List[int]:
        """Get list of neighbors for a node"""
        return list(self.graph.neighbors(node_id))

class CryptocurrencySimulator:
    def __init__(self, n_peers: int, z0: float, z1: float, ttx: float, 
                 block_interval: float, simulation_time: float):
        self.n_peers = n_peers
        self.z0 = z0  # Percentage of slow nodes
        self.z1 = z1  # Percentage of low CPU nodes
        self.ttx = ttx  # Mean transaction inter-arrival time
        self.block_interval = block_interval  # Mean block interval (I)
        self.simulation_time = simulation_time
        
        self.current_time = 0.0
        self.event_queue: List[Event] = []
        self.peers: List[Peer] = []
        self.network: Network = None
        
        # Statistics
        self.total_blocks_generated = defaultdict(int)
        self.blocks_in_longest_chain = defaultdict(int)
        
        self._initialize_network()
        self._schedule_initial_events()
    
    def _initialize_network(self):
        """Initialize peers and network topology"""
        # Create peers with classifications
        n_slow = int(self.n_peers * self.z0 / 100)
        n_low_cpu = int(self.n_peers * self.z1 / 100)
        
        slow_nodes = set(random.sample(range(self.n_peers), n_slow))
        low_cpu_nodes = set(random.sample(range(self.n_peers), n_low_cpu))
        
        total_hash_power = 0
        for i in range(self.n_peers):
            is_slow = i in slow_nodes
            is_low_cpu = i in low_cpu_nodes
            peer = Peer(i, is_slow, is_low_cpu)
            self.peers.append(peer)
            total_hash_power += peer.hash_power
        
        # Normalize hash power
        for peer in self.peers:
            peer.hash_power /= total_hash_power
        
        # Create network topology
        self.network = Network(self.n_peers)
        
        # Set peer connections
        for i in range(self.n_peers):
            neighbors = self.network.get_neighbors(i)
            for neighbor in neighbors:
                self.peers[i].add_peer(neighbor)
    
    def _schedule_initial_events(self):
        """Schedule initial transaction generation events"""
        for i in range(self.n_peers):
            # Schedule first transaction
            next_tx_time = np.random.exponential(self.ttx)
            self._add_event(Event(
                time=next_tx_time,
                event_type=EventType.GENERATE_TRANSACTION,
                node_id=i,
                data={}
            ))
            
            # Schedule initial mining attempt
            self._add_event(Event(
                time=0.1,  # Small delay after genesis
                event_type=EventType.START_MINING,
                node_id=i,
                data={}
            ))
    
    def _add_event(self, event: Event):
        """Add event to the priority queue"""
        heapq.heappush(self.event_queue, event)
    
    def _generate_transaction(self, sender_id: int):
        """Generate a new transaction from sender"""
        # Choose random receiver
        receiver_id = random.choice([i for i in range(self.n_peers) if i != sender_id])
        
        # Get current balance
        longest_chain_txns = self.peers[sender_id].blockchain_tree.get_transactions_in_longest_chain()
        current_balance = self.peers[sender_id].get_balance(longest_chain_txns)
        
        # Choose transaction amount (up to current balance)
        if current_balance > 0:
            amount = random.uniform(0.1, min(current_balance, 50.0))
            
            txn = Transaction(
                txn_id=str(uuid.uuid4())[:8],
                sender_id=sender_id,
                receiver_id=receiver_id,
                amount=round(amount, 2)
            )
            
            # Add to pending transactions
            self.peers[sender_id].pending_transactions.append(txn)
            self.peers[sender_id].seen_transactions.add(txn.txn_id)
            
            # Broadcast transaction
            self._broadcast_transaction(sender_id, txn)
        
        # Schedule next transaction
        next_tx_time = self.current_time + np.random.exponential(self.ttx)
        if next_tx_time < self.simulation_time:
            self._add_event(Event(
                time=next_tx_time,
                event_type=EventType.GENERATE_TRANSACTION,
                node_id=sender_id,
                data={}
            ))
    
    def _broadcast_transaction(self, sender_id: int, transaction: Transaction):
        """Broadcast transaction to connected peers"""
        sender = self.peers[sender_id]
        
        for peer_id in sender.connected_peers:
            latency = self.network.get_latency(
                sender_id, peer_id, transaction.size,
                sender.is_slow, self.peers[peer_id].is_slow
            )
            
            self._add_event(Event(
                time=self.current_time + latency,
                event_type=EventType.RECEIVE_TRANSACTION,
                node_id=peer_id,
                data={'transaction': transaction, 'from': sender_id}
            ))
    
    def _receive_transaction(self, receiver_id: int, transaction: Transaction, from_peer: int):
        """Handle received transaction"""
        receiver = self.peers[receiver_id]
        
        # Skip if already seen
        if transaction.txn_id in receiver.seen_transactions:
            return
        
        receiver.seen_transactions.add(transaction.txn_id)
        receiver.pending_transactions.append(transaction)
        
        # Forward to other peers (except sender)
        for peer_id in receiver.connected_peers:
            if peer_id != from_peer:
                latency = self.network.get_latency(
                    receiver_id, peer_id, transaction.size,
                    receiver.is_slow, self.peers[peer_id].is_slow
                )
                
                self._add_event(Event(
                    time=self.current_time + latency,
                    event_type=EventType.RECEIVE_TRANSACTION,
                    node_id=peer_id,
                    data={'transaction': transaction, 'from': receiver_id}
                ))
    
    def _start_mining(self, miner_id: int):
        """Start mining process for a peer"""
        miner = self.peers[miner_id]
        
        # Create block with valid transactions
        block = self._create_block(miner_id)
        if block is None:
            # Try again later
            self._add_event(Event(
                time=self.current_time + 1.0,
                event_type=EventType.START_MINING,
                node_id=miner_id,
                data={}
            ))
            return
        
        # Calculate mining time
        mining_time = np.random.exponential(self.block_interval / miner.hash_power)
        
        # Schedule block generation
        event_id = str(uuid.uuid4())
        miner.mining_event_id = event_id
        
        self._add_event(Event(
            time=self.current_time + mining_time,
            event_type=EventType.GENERATE_BLOCK,
            node_id=miner_id,
            data={'block': block, 'event_id': event_id}
        ))
    
    def _create_block(self, miner_id: int) -> Optional[Block]:
        """Create a new block with valid transactions"""
        miner = self.peers[miner_id]
        longest_chain_tip = miner.blockchain_tree.longest_chain_tip
        
        # Get transactions in longest chain to check validity
        chain_txns = miner.blockchain_tree.get_transactions_in_longest_chain()
        
        # Create coinbase transaction
        coinbase_tx = Transaction(
            txn_id=str(uuid.uuid4())[:8],
            sender_id=miner_id,
            receiver_id=miner_id,
            amount=50.0
        )
        coinbase_tx.txn_id = f"{miner_id}_mines_50_coins_{coinbase_tx.txn_id}"
        
        valid_transactions = [coinbase_tx]
        current_size = 1024 + coinbase_tx.size  # Base size + coinbase
        
        # Validate and add pending transactions
        for tx in miner.pending_transactions[:]:
            if current_size + tx.size > 8 * 10**6:  # 1MB limit
                break
                
            # Check if transaction is valid (sender has sufficient balance)
            if self._is_transaction_valid(tx, chain_txns + valid_transactions):
                valid_transactions.append(tx)
                current_size += tx.size
                miner.pending_transactions.remove(tx)
        
        return Block(
            block_id=str(uuid.uuid4())[:8],
            prev_block_id=longest_chain_tip,
            transactions=valid_transactions,
            miner_id=miner_id,
            timestamp=self.current_time,
            size=current_size
        )
    
    def _is_transaction_valid(self, tx: Transaction, previous_txns: List[Transaction]) -> bool:
        """Check if transaction is valid given previous transactions"""
        if tx.sender_id == tx.receiver_id and tx.amount != 50.0:  # Allow coinbase
            return False
            
        balance = 1000.0  # Initial balance
        for prev_tx in previous_txns:
            if prev_tx.sender_id == tx.sender_id:
                balance -= prev_tx.amount
            if prev_tx.receiver_id == tx.sender_id:
                balance += prev_tx.amount
        
        return balance >= tx.amount
    
    def _generate_block(self, miner_id: int, block: Block, event_id: str):
        """Generate and broadcast a new block"""
        miner = self.peers[miner_id]
        
        # Check if this mining event is still valid
        if miner.mining_event_id != event_id:
            return  # Mining was cancelled
        
        # Check if still mining on the same chain tip
        if block.prev_block_id != miner.blockchain_tree.longest_chain_tip:
            # Chain changed, start mining again
            self._start_mining(miner_id)
            return
        
        # Add block to own blockchain
        miner.blockchain_tree.add_block(block, self.current_time)
        miner.seen_blocks.add(block.block_id)
        
        # Statistics
        self.total_blocks_generated[miner_id] += 1
        
        # Broadcast block
        self._broadcast_block(miner_id, block)
        
        # Start mining next block
        self._start_mining(miner_id)
    
    def _broadcast_block(self, sender_id: int, block: Block):
        """Broadcast block to connected peers"""
        sender = self.peers[sender_id]
        
        for peer_id in sender.connected_peers:
            latency = self.network.get_latency(
                sender_id, peer_id, block.size,
                sender.is_slow, self.peers[peer_id].is_slow
            )
            
            self._add_event(Event(
                time=self.current_time + latency,
                event_type=EventType.RECEIVE_BLOCK,
                node_id=peer_id,
                data={'block': block, 'from': sender_id}
            ))
    
    def _receive_block(self, receiver_id: int, block: Block, from_peer: int):
        """Handle received block"""
        receiver = self.peers[receiver_id]
        
        # Skip if already seen
        if block.block_id in receiver.seen_blocks:
            return
        
        receiver.seen_blocks.add(block.block_id)
        
        # Validate block transactions
        if not self._validate_block(block, receiver):
            return
        
        # Add to blockchain tree
        chain_extended = receiver.blockchain_tree.add_block(block, self.current_time)
        
        # If longest chain changed, cancel current mining and start new
        if chain_extended:
            receiver.mining_event_id = None  # Cancel current mining
            self._start_mining(receiver_id)
        
        # Forward block to other peers
        for peer_id in receiver.connected_peers:
            if peer_id != from_peer:
                latency = self.network.get_latency(
                    receiver_id, peer_id, block.size,
                    receiver.is_slow, self.peers[peer_id].is_slow
                )
                
                self._add_event(Event(
                    time=self.current_time + latency,
                    event_type=EventType.RECEIVE_BLOCK,
                    node_id=peer_id,
                    data={'block': block, 'from': receiver_id}
                ))
    
    def _validate_block(self, block: Block, receiver: Peer) -> bool:
        """Validate a received block"""
        # Check if parent exists
        if block.prev_block_id not in receiver.blockchain_tree.blocks:
            return False
        
        # Validate all transactions in the block
        # Get chain up to parent block
        parent_chain_txns = []
        current = block.prev_block_id
        while current != "" and current in receiver.blockchain_tree.blocks:
            if current != "genesis":
                parent_chain_txns.extend(receiver.blockchain_tree.blocks[current].transactions)
            current = receiver.blockchain_tree.parent.get(current, "")
        
        # Validate each transaction
        for tx in block.transactions:
            if not self._is_transaction_valid(tx, parent_chain_txns):
                return False
            parent_chain_txns.append(tx)  # Add for next validation
        
        return True
    
    def run(self):
        """Run the simulation"""
        print(f"Starting simulation with {self.n_peers} peers...")
        print(f"Slow nodes: {self.z0}%, Low CPU nodes: {self.z1}%")
        
        while self.event_queue and self.current_time < self.simulation_time:
            event = heapq.heappop(self.event_queue)
            self.current_time = event.time
            
            if self.current_time >= self.simulation_time:
                break
            
            # Process event
            if event.event_type == EventType.GENERATE_TRANSACTION:
                self._generate_transaction(event.node_id)
            elif event.event_type == EventType.RECEIVE_TRANSACTION:
                self._receive_transaction(
                    event.node_id, 
                    event.data['transaction'], 
                    event.data['from']
                )
            elif event.event_type == EventType.START_MINING:
                self._start_mining(event.node_id)
            elif event.event_type == EventType.GENERATE_BLOCK:
                self._generate_block(
                    event.node_id, 
                    event.data['block'], 
                    event.data['event_id']
                )
            elif event.event_type == EventType.RECEIVE_BLOCK:
                self._receive_block(
                    event.node_id, 
                    event.data['block'], 
                    event.data['from']
                )
        
        print(f"Simulation completed at time {self.current_time:.2f}")
        self._calculate_statistics()
    
    def _calculate_statistics(self):
        """Calculate final statistics"""
        # Find blocks in longest chain for each peer
        for peer in self.peers:
            for block_id in peer.blockchain_tree.get_longest_chain():
                if block_id != "genesis":
                    block = peer.blockchain_tree.blocks[block_id]
                    if block.miner_id == peer.peer_id:
                        self.blocks_in_longest_chain[peer.peer_id] += 1

    
    def print_statistics(self):
        """Print simulation statistics"""
        print("\n=== SIMULATION STATISTICS ===")
        print(f"Total simulation time: {self.current_time:.2f} seconds")
        
        print(f"\nPeer Classifications:")
        slow_count = sum(1 for p in self.peers if p.is_slow)
        low_cpu_count = sum(1 for p in self.peers if p.is_low_cpu)
        print(f"Slow peers: {slow_count}/{self.n_peers} ({slow_count/self.n_peers*100:.1f}%)")
        print(f"Low CPU peers: {low_cpu_count}/{self.n_peers} ({low_cpu_count/self.n_peers*100:.1f}%)")
        
        print(f"\nBlock Generation Statistics:")
        print(f"{'Peer':<6} {'Type':<15} {'Total':<8} {'InChain':<8} {'Ratio':<8} {'HashPower':<10}")
        print("-" * 65)
        
        for i, peer in enumerate(self.peers):
            peer_type = ""
            if peer.is_slow and peer.is_low_cpu:
                peer_type = "Slow+LowCPU"
            elif peer.is_slow:
                peer_type = "Slow"
            elif peer.is_low_cpu:
                peer_type = "LowCPU"
            else:
                peer_type = "Fast+HighCPU"
            
            total_blocks = self.total_blocks_generated[i]
            chain_blocks = self.blocks_in_longest_chain[i]
            ratio = chain_blocks / total_blocks if total_blocks > 0 else 0
            
            print(f"{i:<6} {peer_type:<15} {total_blocks:<8} {chain_blocks:<8} {ratio:<8.3f} {peer.hash_power:<10.3f}")
        
        # Analyze by peer type
        print(f"\nAnalysis by Peer Type:")
        types = {
            'Fast+HighCPU': [],
            'Fast+LowCPU': [],
            'Slow+HighCPU': [],
            'Slow+LowCPU': []
        }
        
        for i, peer in enumerate(self.peers):
            if peer.is_slow and peer.is_low_cpu:
                key = 'Slow+LowCPU'
            elif peer.is_slow:
                key = 'Slow+HighCPU'
            elif peer.is_low_cpu:
                key = 'Fast+LowCPU'
            else:
                key = 'Fast+HighCPU'
            
            total = self.total_blocks_generated[i]
            chain = self.blocks_in_longest_chain[i]
            ratio = chain / total if total > 0 else 0
            types[key].append((total, chain, ratio))
        
        for peer_type, data in types.items():
            if data:
                avg_ratio = sum(d[2] for d in data) / len(data)
                total_generated = sum(d[0] for d in data)
                total_in_chain = sum(d[1] for d in data)
                print(f"{peer_type}: Avg ratio = {avg_ratio:.3f}, Total blocks = {total_generated}, In chain = {total_in_chain}")
        
        # Blockchain tree analysis
        sample_peer = self.peers[0]
        longest_chain = sample_peer.blockchain_tree.get_longest_chain()
        print(f"\nBlockchain Analysis:")
        print(f"Longest chain length: {len(longest_chain)} blocks")
        
        # Calculate branch lengths
        all_blocks = set(sample_peer.blockchain_tree.blocks.keys())
        longest_chain_set = set(longest_chain)
        orphaned_blocks = all_blocks - longest_chain_set
        print(f"Total blocks: {len(all_blocks)}")
        print(f"Orphaned blocks: {len(orphaned_blocks)}")
        print(f"Efficiency: {len(longest_chain_set)/len(all_blocks)*100:.1f}%")
    
    def save_blockchain_data(self, filename: str):
        """Save blockchain data for visualization"""
        # Use first peer's blockchain tree as reference
        peer = self.peers[0]
        
        # Create data structure for visualization
        data = {
            'blocks': {},
            'edges': [],
            'longest_chain': peer.blockchain_tree.get_longest_chain(),
            'statistics': {
                'total_blocks_generated': dict(self.total_blocks_generated),
                'blocks_in_longest_chain': dict(self.blocks_in_longest_chain),
                'peer_types': {}
            }
        }
        
        # Add peer type information
        for i, p in enumerate(self.peers):
            data['statistics']['peer_types'][i] = {
                'is_slow': p.is_slow,
                'is_low_cpu': p.is_low_cpu,
                'hash_power': p.hash_power
            }
        
        # Add block information
        for block_id, block in peer.blockchain_tree.blocks.items():
            data['blocks'][block_id] = {
                'miner_id': block.miner_id,
                'timestamp': block.timestamp,
                'size': block.size,
                'num_transactions': len(block.transactions),
                'arrival_time': peer.blockchain_tree.block_arrival_times.get(block_id, 0)
            }
            
            # Add edge to parent
            if block.prev_block_id:
                data['edges'].append([block.prev_block_id, block_id])
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"Blockchain data saved to {filename}")

def main():
    parser = argparse.ArgumentParser(description='P2P Cryptocurrency Network Simulator')
    parser.add_argument('--n', type=int, default=20, help='Number of peers')
    parser.add_argument('--z0', type=float, default=40, help='Percentage of slow peers')
    parser.add_argument('--z1', type=float, default=40, help='Percentage of low CPU peers')
    parser.add_argument('--ttx', type=float, default=1.0, help='Mean transaction inter-arrival time (seconds)')
    parser.add_argument('--I', type=float, default=600, help='Mean block interval (seconds)')
    parser.add_argument('--sim-time', type=float, default=3000, help='Simulation time (seconds)')
    parser.add_argument('--output', type=str, default='blockchain_data.json', help='Output file for blockchain data')
    
    args = parser.parse_args()
    
    # Create and run simulator
    simulator = CryptocurrencySimulator(
        n_peers=args.n,
        z0=args.z0,
        z1=args.z1,
        ttx=args.ttx,
        block_interval=args.I,
        simulation_time=args.sim_time
    )
    
    start_time = time.time()
    simulator.run()
    end_time = time.time()
    
    print(f"\nSimulation completed in {end_time - start_time:.2f} seconds")
    
    simulator.print_statistics()
    simulator.save_blockchain_data(args.output)

if __name__ == "__main__":
    main()