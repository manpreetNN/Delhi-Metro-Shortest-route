class RouteFormatter:
    @staticmethod
    def calculate_fare(distance_km):
        """Calculates DMRC fare based on revised route distance slabs (km)."""
        if distance_km <= 2.0:
            return 11
        elif distance_km <= 5.0:
            return 21
        elif distance_km <= 12.0:
            return 32
        elif distance_km <= 21.0:
            return 43
        elif distance_km <= 32.0:
            return 54
        else:
            return 64

    @staticmethod
    def generate_step_by_step(path_nodes, data_loader):
        """
        Formats split-node paths (e.g. 'Azadpur_Yellow Line') into clean step-by-step UI directions.
        """
        if not path_nodes or len(path_nodes) < 2:
            return [], []

        directions = []
        interchanges = []

        # Skip any leading same-station transfer at the starting station
        start_idx = 0
        if len(path_nodes) >= 2:
            st0, _ = path_nodes[0].rsplit('_', 1)
            st1, _ = path_nodes[1].rsplit('_', 1)
            if st0 == st1:
                start_idx = 1

        # Remove trailing same-station transfer at the destination station if any
        end_idx = len(path_nodes)
        if end_idx - start_idx >= 2:
            st_last, _ = path_nodes[-1].rsplit('_', 1)
            st_prev, _ = path_nodes[-2].rsplit('_', 1)
            if st_last == st_prev:
                end_idx -= 1

        first_station, current_line = path_nodes[start_idx].rsplit('_', 1)
        directions.append(f"Board {current_line} at '{first_station}'")

        for i in range(start_idx + 1, end_idx):
            prev_station, prev_line = path_nodes[i - 1].rsplit('_', 1)
            curr_station, curr_line = path_nodes[i].rsplit('_', 1)

            if prev_station == curr_station and prev_line != curr_line:
                interchanges.append(curr_station)
                directions.append(f"--- INTERCHANGE at '{curr_station}': Switch from {prev_line} to {curr_line} ---")
                current_line = curr_line
            elif prev_line != curr_line:
                interchanges.append(f"{prev_station} -> {curr_station}")
                directions.append(f"--- INTERCHANGE WALKWAY: Walk from '{prev_station}' ({prev_line}) to '{curr_station}' ({curr_line}) ---")
                current_line = curr_line
            else:
                directions.append(f"  -> Ride to '{curr_station}' ({curr_line})")

        return directions, interchanges