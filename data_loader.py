import csv
from collections import defaultdict
from itertools import combinations

class DataLoader:
    def __init__(self, csv_filepath="delhi_metro_network.csv"):
        self.csv_filepath = csv_filepath
        self.network_data = []
        self.node_names = []
        self.name_to_idx = {}
        self.idx_to_name = {}

    def load_and_preprocess(self):
        nodes_set = set()
        self.network_data = []
        station_to_lines = defaultdict(set)
        walkway_rows = []

        try:
            with open(self.csv_filepath, mode='r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if not row or row.get('Distance_km') is None or str(row.get('Distance_km')).strip() == '':
                        continue

                    row['Distance_km'] = float(row['Distance_km'])
                    row['Travel_Time_min'] = float(row['Travel_Time_min'])

                    if row['Line'] == 'Interchange Walkway':
                        walkway_rows.append(row)
                        continue
                    
                    # 1. NODE SPLITTING: Append Line to Station Name
                    src_node = f"{row['Source_Station']}_{row['Line']}"
                    dst_node = f"{row['Destination_Station']}_{row['Line']}"
                    
                    row['Source_Node'] = src_node
                    row['Destination_Node'] = dst_node
                    
                    self.network_data.append(row)
                    nodes_set.add(src_node)
                    nodes_set.add(dst_node)
                    
                    station_to_lines[row['Source_Station']].add(row['Line'])
                    station_to_lines[row['Destination_Station']].add(row['Line'])
        except FileNotFoundError:
            raise FileNotFoundError(f"CSV file '{self.csv_filepath}' not found.")

        # 2. READ CUSTOM SAME-STATION TRANSFER TIMES FROM CSV (IF PRESENT)
        custom_penalty = {}
        external_walkways = []
        for row in walkway_rows:
            if row['Source_Station'] == row['Destination_Station']:
                custom_penalty[row['Source_Station']] = row['Travel_Time_min']
            else:
                external_walkways.append(row)

        # 3. INJECT SAME-STATION WALKING EDGES (DEFAULT 5.0 MINS IF NOT IN CSV)
        for station, lines in station_to_lines.items():
            if len(lines) > 1:
                penalty = custom_penalty.get(station, 5.0)
                for line_a, line_b in combinations(sorted(lines), 2):
                    node_a = f"{station}_{line_a}"
                    node_b = f"{station}_{line_b}"
                    
                    self.network_data.append({
                        'Source_Station': station, 'Destination_Station': station,
                        'Source_Node': node_a, 'Destination_Node': node_b,
                        'Line': 'Interchange Walkway',
                        'Distance_km': 0.0, 'Travel_Time_min': penalty
                    })
                    self.network_data.append({
                        'Source_Station': station, 'Destination_Station': station,
                        'Source_Node': node_b, 'Destination_Node': node_a,
                        'Line': 'Interchange Walkway',
                        'Distance_km': 0.0, 'Travel_Time_min': penalty
                    })

        # 4. CONNECT OUT-OF-STATION WALKWAYS (e.g., Dhaula Kuan <-> South Campus, Sec 52 <-> Sec 51)
        for row in external_walkways:
            u_st, v_st = row['Source_Station'], row['Destination_Station']
            for line_u in station_to_lines.get(u_st, []):
                for line_v in station_to_lines.get(v_st, []):
                    self.network_data.append({
                        'Source_Station': u_st, 'Destination_Station': v_st,
                        'Source_Node': f"{u_st}_{line_u}", 'Destination_Node': f"{v_st}_{line_v}",
                        'Line': 'Interchange Walkway',
                        'Distance_km': row['Distance_km'], 'Travel_Time_min': row['Travel_Time_min']
                    })

        self.node_names = sorted(list(nodes_set))
        self.name_to_idx = {name: idx for idx, name in enumerate(self.node_names)}
        self.idx_to_name = {idx: name for idx, name in enumerate(self.node_names)}

        return self.network_data, self.node_names, self.name_to_idx, self.idx_to_name

    def get_edge_line(self, src_name, dst_name):
        """Returns the metro line connecting two nodes or stations."""
        for row in self.network_data:
            if row.get('Source_Node') == src_name and row.get('Destination_Node') == dst_name:
                return row['Line']
            if row['Source_Station'] == src_name and row['Destination_Station'] == dst_name and row['Line'] != 'Interchange Walkway':
                return row['Line']
        return "Interchange Walkway"