import json
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from collections import defaultdict
import argparse

class BlockchainVisualizer:
    def __init__(self, data_file):
        with open(data_file, 'r') as f:
            self.data = json.load(f)
        
        self.blocks = self.data['blocks']
        self.edges = self.data['edges']
        self.longest_chain = self.data['longest_chain']
        self.stats = self.data['statistics']
    
    def create_blockchain_graph(self):
        """Create NetworkX graph from blockchain data"""
        G = nx.DiGraph()
        
        # Add nodes (blocks)
        for block_id, block_info in self.blocks.items():
            G.add_node(block_id, **block_info)
        
        # Add edges (parent-child relationships)
        for parent, child in self.edges:
            G.add_edge(parent, child)
        
        return G
    
    def visualize_blockchain_tree(self, save_path=None):
        """Visualize the blockchain tree structure"""
        G = self.create_blockchain_graph()
        
        plt.figure(figsize=(15, 10))
        
        # Create layout
        pos = self._create_hierarchical_layout(G)
        
        # Color nodes based on whether they're in longest chain
        node_colors = []
        node_sizes = []
        for node in G.nodes():
            if node in self.longest_chain:
                node_colors.append('lightgreen')
                node_sizes.append(800)
            else:
                node_colors.append('lightcoral')
                node_sizes.append(600)
        
        # Draw the graph
        nx.draw(G, pos, 
                node_color=node_colors,
                node_size=node_sizes,
                with_labels=True,
                labels={node: node[:8] for node in G.nodes()},
                font_size=8,
                font_weight='bold',
                arrows=True,
                arrowsize=20,
                edge_color='gray',
                alpha=0.7)
        
        plt.title("Blockchain Tree Structure\n(Green: Longest Chain, Red: Orphaned Blocks)", 
                 fontsize=14, fontweight='bold')
        plt.axis('off')
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def _create_hierarchical_layout(self, G):
        """Create a hierarchical layout for the blockchain tree"""
        # Find the root (genesis block)
        root = 'genesis'
        
        # Calculate levels for each node
        levels = {}
        queue = [(root, 0)]
        
        while queue:
            node, level = queue.pop(0)
            if node not in levels:
                levels[node] = level
                for successor in G.successors(node):
                    queue.append((successor, level + 1))
        
        # Group nodes by level
        level_groups = defaultdict(list)
        for node, level in levels.items():
            level_groups[level].append(node)
        
        # Create positions
        pos = {}
        max_level = max(levels.values())
        
        for level, nodes in level_groups.items():
            y = max_level - level  # Flip so genesis is at top
            
            if len(nodes) == 1:
                pos[nodes[0]] = (0, y)
            else:
                x_positions = np.linspace(-len(nodes)/2, len(nodes)/2, len(nodes))
                for i, node in enumerate(nodes):
                    pos[node] = (x_positions[i], y)
        
        return pos
    
    def plot_mining_statistics(self, save_path=None):
        """Plot mining statistics by peer type"""
        # Prepare data
        peer_types = []
        ratios = []
        hash_powers = []
        total_blocks = []
        
        for peer_id, peer_info in self.stats['peer_types'].items():
            peer_id = int(peer_id)
            
            # Determine peer type
            if peer_info['is_slow'] and peer_info['is_low_cpu']:
                peer_type = 'Slow+LowCPU'
            elif peer_info['is_slow']:
                peer_type = 'Slow+HighCPU'
            elif peer_info['is_low_cpu']:
                peer_type = 'Fast+LowCPU'
            else:
                peer_type = 'Fast+HighCPU'
            
            peer_types.append(peer_type)
            
            total = self.stats['total_blocks_generated'].get(str(peer_id), 0)
            in_chain = self.stats['blocks_in_longest_chain'].get(str(peer_id), 0)
            ratio = in_chain / total if total > 0 else 0
            
            ratios.append(ratio)
            hash_powers.append(peer_info['hash_power'])
            total_blocks.append(total)
        
        # Create subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Plot 1: Ratio by peer type
        type_ratios = defaultdict(list)
        for ptype, ratio in zip(peer_types, ratios):
            type_ratios[ptype].append(ratio)
        
        types = list(type_ratios.keys())
        avg_ratios = [np.mean(type_ratios[t]) for t in types]
        
        ax1.bar(types, avg_ratios, color=['skyblue', 'lightgreen', 'orange', 'pink'])
        ax1.set_title('Average Block Inclusion Ratio by Peer Type')
        ax1.set_ylabel('Ratio (Blocks in Chain / Total Blocks)')
        ax1.set_ylim(0, 1)
        ax1.tick_params(axis='x', rotation=45)
        
        # Plot 2: Hash power distribution
        ax2.scatter(hash_powers, ratios, c=[plt.cm.Set1(i) for i in range(len(peer_types))], alpha=0.7)
        ax2.set_xlabel('Hash Power')
        ax2.set_ylabel('Block Inclusion Ratio')
        ax2.set_title('Block Inclusion Ratio vs Hash Power')
        
        # Plot 3: Total blocks by peer type
        type_blocks = defaultdict(list)
        for ptype, blocks in zip(peer_types, total_blocks):
            type_blocks[ptype].append(blocks)
        
        avg_blocks = [np.mean(type_blocks[t]) for t in types]
        ax3.bar(types, avg_blocks, color=['skyblue', 'lightgreen', 'orange', 'pink'])
        ax3.set_title('Average Total Blocks Generated by Peer Type')
        ax3.set_ylabel('Average Blocks Generated')
        ax3.tick_params(axis='x', rotation=45)
        
        # Plot 4: Individual peer performance
        peer_ids = list(range(len(ratios)))
        colors = ['red' if 'Slow' in pt else 'blue' for pt in peer_types]
        ax4.scatter(peer_ids, ratios, c=colors, alpha=0.7)
        ax4.set_xlabel('Peer ID')
        ax4.set_ylabel('Block Inclusion Ratio')
        ax4.set_title('Individual Peer Performance (Red: Slow, Blue: Fast)')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
        plt.show()
    
    def analyze_blockchain_structure(self):
        """Analyze and print blockchain structure statistics"""
        print("=== BLOCKCHAIN STRUCTURE ANALYSIS ===")
        
        G = self.create_blockchain_graph()
        
        # Basic statistics
        total_blocks = len(self.blocks)
        longest_chain_length = len(self.longest_chain)
        orphaned_blocks = total_blocks - longest_chain_length
        
        print(f"Total blocks: {total_blocks}")
        print(f"Longest chain length: {longest_chain_length}")
        print(f"Orphaned blocks: {orphaned_blocks}")
        print(f"Blockchain efficiency: {longest_chain_length/total_blocks*100:.1f}%")
        
        # Branch analysis
        branches = self._analyze_branches(G)
        print(f"\nBranch Analysis:")
        print(f"Number of branches: {len(branches)}")
        if branches:
            branch_lengths = [len(branch) for branch in branches]
            print(f"Average branch length: {np.mean(branch_lengths):.1f} blocks")
            print(f"Maximum branch length: {max(branch_lengths)} blocks")
            print(f"Minimum branch length: {min(branch_lengths)} blocks")
        
        # Mining distribution
        print(f"\nMining Distribution:")
        miner_blocks = defaultdict(int)
        for block_id, block_info in self.blocks.items():
            if block_id != 'genesis':
                miner_blocks[block_info['miner_id']] += 1
        
        print(f"Most active miner: Peer {max(miner_blocks, key=miner_blocks.get)} "
              f"({miner_blocks[max(miner_blocks, key=miner_blocks.get)]} blocks)")
        print(f"Least active miner: Peer {min(miner_blocks, key=miner_blocks.get)} "
              f"({miner_blocks[min(miner_blocks, key=miner_blocks.get)]} blocks)")
        
        # Timing analysis
        timestamps = [block_info['timestamp'] for block_id, block_info in self.blocks.items() 
                     if block_id != 'genesis']
        if timestamps:
            print(f"\nTiming Analysis:")
            print(f"First block timestamp: {min(timestamps):.1f}s")
            print(f"Last block timestamp: {max(timestamps):.1f}s")
            print(f"Average block interval: {np.mean(np.diff(sorted(timestamps))):.1f}s")
    
    def _analyze_branches(self, G):
        """Find all branches (paths not in longest chain)"""
        longest_chain_set = set(self.longest_chain)
        branches = []
        
        # Find all leaf nodes
        leaf_nodes = [node for node in G.nodes() if G.out_degree(node) == 0]
        
        for leaf in leaf_nodes:
            if leaf not in longest_chain_set:
                # Trace back to find the branch
                branch = []
                current = leaf
                
                while current and current not in longest_chain_set:
                    branch.append(current)
                    predecessors = list(G.predecessors(current))
                    current = predecessors[0] if predecessors else None
                
                if len(branch) > 1:  # Only consider branches with more than 1 block
                    branches.append(branch)
        
        return branches
    
    def plot_network_topology(self, save_path=None):
        """Visualize the P2P network topology"""
        # This would require network topology data
        # For now, we'll create a simple visualization showing peer connections
        print("Network topology visualization would require additional network data.")
        print("The simulator saves blockchain data but not the detailed network topology.")
    
    def generate_report(self, output_file='blockchain_analysis_report.txt'):
        """Generate a comprehensive analysis report"""
        with open(output_file, 'w') as f:
            f.write("BLOCKCHAIN SIMULATION ANALYSIS REPORT\n")
            f.write("=" * 50 + "\n\n")
            
            # Basic statistics
            f.write("1. BASIC STATISTICS\n")
            f.write("-" * 20 + "\n")
            total_blocks = len(self.blocks)
            longest_chain_length = len(self.longest_chain)
            f.write(f"Total blocks generated: {total_blocks}\n")
            f.write(f"Longest chain length: {longest_chain_length}\n")
            f.write(f"Orphaned blocks: {total_blocks - longest_chain_length}\n")
            f.write(f"Blockchain efficiency: {longest_chain_length/total_blocks*100:.1f}%\n\n")
            
            # Peer type analysis
            f.write("2. PEER TYPE ANALYSIS\n")
            f.write("-" * 22 + "\n")
            
            type_stats = defaultdict(lambda: {'count': 0, 'total_blocks': 0, 'chain_blocks': 0, 'ratios': []})
            
            for peer_id, peer_info in self.stats['peer_types'].items():
                peer_id = int(peer_id)
                
                if peer_info['is_slow'] and peer_info['is_low_cpu']:
                    peer_type = 'Slow+LowCPU'
                elif peer_info['is_slow']:
                    peer_type = 'Slow+HighCPU'
                elif peer_info['is_low_cpu']:
                    peer_type = 'Fast+LowCPU'
                else:
                    peer_type = 'Fast+HighCPU'
                
                total = self.stats['total_blocks_generated'].get(str(peer_id), 0)
                in_chain = self.stats['blocks_in_longest_chain'].get(str(peer_id), 0)
                ratio = in_chain / total if total > 0 else 0
                
                type_stats[peer_type]['count'] += 1
                type_stats[peer_type]['total_blocks'] += total
                type_stats[peer_type]['chain_blocks'] += in_chain
                type_stats[peer_type]['ratios'].append(ratio)
            
            for peer_type, stats in type_stats.items():
                if stats['count'] > 0:
                    avg_ratio = np.mean(stats['ratios'])
                    f.write(f"{peer_type}:\n")
                    f.write(f"  Count: {stats['count']}\n")
                    f.write(f"  Total blocks: {stats['total_blocks']}\n")
                    f.write(f"  Blocks in chain: {stats['chain_blocks']}\n")
                    f.write(f"  Average inclusion ratio: {avg_ratio:.3f}\n\n")
            
            # Mining performance insights
            f.write("3. INSIGHTS AND OBSERVATIONS\n")
            f.write("-" * 30 + "\n")
            
            f.write("Key Observations:\n")
            f.write("- High CPU nodes should have higher block inclusion ratios\n")
            f.write("- Fast nodes should have better network propagation\n")
            f.write("- Nodes with higher hash power should mine more blocks\n")
            f.write("- Fork resolution should favor the longest chain\n\n")
            
            # Theoretical explanations
            f.write("4. THEORETICAL EXPLANATIONS\n")
            f.write("-" * 31 + "\n")
            
            f.write("Exponential Distribution for Transaction Inter-arrival:\n")
            f.write("- Models memoryless arrival process\n")
            f.write("- Common in queueing theory for independent events\n")
            f.write("- Realistic for decentralized transaction generation\n\n")
            
            f.write("Exponential Distribution for Mining Time:\n")
            f.write("- Models Poisson process for block discovery\n")
            f.write("- Reflects the random nature of PoW mining\n")
            f.write("- Rate inversely proportional to hash power\n\n")
            
            f.write("Queuing Delay Inversely Related to Link Speed:\n")
            f.write("- Higher bandwidth = faster message processing\n")
            f.write("- Queuing delay represents network congestion\n")
            f.write("- Slower links have longer queues\n")
        
        print(f"Analysis report saved to {output_file}")

def main():
    parser = argparse.ArgumentParser(description='Blockchain Visualization Tool')
    parser.add_argument('data_file', help='JSON file containing blockchain data')
    parser.add_argument('--tree', action='store_true', help='Show blockchain tree visualization')
    parser.add_argument('--stats', action='store_true', help='Show mining statistics plots')
    parser.add_argument('--analysis', action='store_true', help='Print detailed analysis')
    parser.add_argument('--report', action='store_true', help='Generate analysis report')
    parser.add_argument('--all', action='store_true', help='Show all visualizations and analysis')
    parser.add_argument('--save-dir', default='.', help='Directory to save plots')
    
    args = parser.parse_args()
    
    try:
        visualizer = BlockchainVisualizer(args.data_file)
        
        if args.all or args.tree:
            print("Generating blockchain tree visualization...")
            save_path = f"{args.save_dir}/blockchain_tree.png" if args.save_dir != '.' else None
            visualizer.visualize_blockchain_tree(save_path)
        
        if args.all or args.stats:
            print("Generating mining statistics plots...")
            save_path = f"{args.save_dir}/mining_stats.png" if args.save_dir != '.' else None
            visualizer.plot_mining_statistics(save_path)
        
        if args.all or args.analysis:
            print("Performing blockchain structure analysis...")
            visualizer.analyze_blockchain_structure()
        
        if args.all or args.report:
            print("Generating comprehensive analysis report...")
            visualizer.generate_report()
        
        if not any([args.tree, args.stats, args.analysis, args.report, args.all]):
            print("No visualization option selected. Use --help for options.")
            print("Available options: --tree, --stats, --analysis, --report, --all")
    
    except FileNotFoundError:
        print(f"Error: Could not find data file {args.data_file}")
        print("Make sure to run the simulator first to generate blockchain data.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()