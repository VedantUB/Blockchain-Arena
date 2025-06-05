import random
import networkx as nx
import matplotlib.pyplot as plt

class Network:
    def __init__(self):
        self.min_nodes = 50
        self.max_nodes = 100
        self.min_degree = 3
        self.max_degree = 6
        self.graph = nx.Graph()
        self.generate_valid_network()

    def generate_valid_network(self):
        while True:
            self.graph.clear()
            num_nodes = random.randint(self.min_nodes, self.max_nodes)
            self.graph.add_nodes_from(range(num_nodes))
            
            nodes = list(self.graph.nodes)
            random.shuffle(nodes)
            for i in range(1, num_nodes):
                u = nodes[i]
                v = random.choice(nodes[:i])
                self.graph.add_edge(u, v)
            
            self._add_random_edges()
           
            if self._is_valid():
                break

    def _add_random_edges(self):
        attempts = 0
        max_attempts = 10000
        nodes = list(self.graph.nodes)
        while attempts < max_attempts:
            u, v = random.sample(nodes, 2)
            if not self.graph.has_edge(u, v):
                if self.graph.degree[u] < self.max_degree and self.graph.degree[v] < self.max_degree:
                    self.graph.add_edge(u, v)
            attempts += 1

    def _is_valid(self):
        # Checking connectivity
        if not nx.is_connected(self.graph):
            return False

        # Checking all node degrees
        for node in self.graph.nodes:
            deg = self.graph.degree[node]
            if deg < self.min_degree or deg > self.max_degree:
                return False

        return True

    def visualize(self, filename='network.png'):
        plt.figure(figsize=(12, 8))
        pos = nx.spring_layout(self.graph, seed=42)
        nx.draw(self.graph, pos, with_labels=True, node_size=300, node_color='skyblue', edge_color='gray')
        plt.title("Undirected P2P Network")
        plt.savefig(filename)
        plt.show()


if __name__ == "__main__":
    net = Network()
    net.visualize()
