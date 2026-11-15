from data_loader import DataLoader

class MetroBackend:
    def __init__(self, csv_filepath="delhi_metro_network.csv"):
        self.data_loader = DataLoader(csv_filepath)
        self.network_data, self.node_names, self.name_to_idx, self.idx_to_name = self.data_loader.load_and_preprocess()
        self.INF = float('inf')
        
        # Provide base station names (without line suffix) for the frontend dropdown UI
        base_stations = set(node.rsplit('_', 1)[0] for node in self.node_names)
        self.station_names = sorted(list(base_stations))
        
        self.run_floyd_warshall()

    def run_floyd_warshall(self):
        V = len(self.node_names)
        self.dist = [[self.INF] * V for _ in range(V)]
        self.dist_km_matrix = [[self.INF] * V for _ in range(V)]
        self.next_node = [[-1] * V for _ in range(V)]

        for i in range(V):
            self.dist[i][i] = 0.0
            self.dist_km_matrix[i][i] = 0.0
            self.next_node[i][i] = i

        for row in self.network_data:
            u = self.name_to_idx[row['Source_Node']]
            v = self.name_to_idx[row['Destination_Node']]
            weight_time = row['Travel_Time_min']
            weight_dist = row['Distance_km']

            if weight_time < self.dist[u][v]:
                self.dist[u][v] = weight_time
                self.dist_km_matrix[u][v] = weight_dist
                self.next_node[u][v] = v

        for k in range(V):
            for i in range(V):
                for j in range(V):
                    if self.dist[i][k] + self.dist[k][j] < self.dist[i][j]:
                        self.dist[i][j] = self.dist[i][k] + self.dist[k][j]
                        self.dist_km_matrix[i][j] = self.dist_km_matrix[i][k] + self.dist_km_matrix[k][j]
                        self.next_node[i][j] = self.next_node[i][k]

    def get_shortest_path(self, src_base_name, dst_base_name):
        """Returns total time (mins), route node list, and distance (km)."""
        src_nodes = [idx for name, idx in self.name_to_idx.items() if name.rsplit('_', 1)[0] == src_base_name]
        dst_nodes = [idx for name, idx in self.name_to_idx.items() if name.rsplit('_', 1)[0] == dst_base_name]

        if not src_nodes or not dst_nodes:
            return None, [], 0.0

        best_time = self.INF
        best_u, best_v = -1, -1

        for u in src_nodes:
            for v in dst_nodes:
                if self.dist[u][v] < best_time:
                    best_time = self.dist[u][v]
                    best_u = u
                    best_v = v

        if best_time == self.INF:
            return None, [], 0.0

        path = [best_u]
        curr = best_u
        while curr != best_v:
            curr = self.next_node[curr][best_v]
            path.append(curr)

        node_path = [self.idx_to_name[idx] for idx in path]
        return best_time, node_path, self.dist_km_matrix[best_u][best_v]