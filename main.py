import os
import json
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs
from metro_backend import MetroBackend
from route_formatter import RouteFormatter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

csv_path = os.path.join(BASE_DIR, "delhi_network.csv")
if not os.path.exists(csv_path):
    csv_path = os.path.join(BASE_DIR, "delhi_metro_network.csv")

print("Initializing Delhi Metro Optimization System...")
backend = MetroBackend(csv_path)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        url = urlparse(self.path)

        if url.path == "/":
            with open(os.path.join(BASE_DIR, "index.html"), "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(data)

        elif url.path in ("/metro_map.png", "/metro_map.jpg"):
            img_name = "metro_map.png" if os.path.exists(os.path.join(BASE_DIR, "metro_map.png")) else "metro_map.jpg"
            img_path = os.path.join(BASE_DIR, img_name)
            if os.path.exists(img_path):
                with open(img_path, "rb") as f:
                    data = f.read()
                mime = "image/png" if img_name.endswith(".png") else "image/jpeg"
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.end_headers()
                self.wfile.write(data)

        elif url.path == "/stations":
            self._json({"stations": backend.station_names})

        elif url.path == "/route":
            q = parse_qs(url.query)
            src = q.get("src", [""])[0]
            dst = q.get("dst", [""])[0]
            time_min, path, dist_km = backend.get_shortest_path(src, dst)

            if not path:
                return self._json({"error": "No route found between selected stations."})

            steps, interchanges = RouteFormatter.generate_step_by_step(path, backend.data_loader)
            
            # Count unique physical stations along the path so same-station transfers aren't double-counted
            unique_stops = [path[0].rsplit('_', 1)[0]]
            for node in path[1:]:
                st_name = node.rsplit('_', 1)[0]
                if st_name != unique_stops[-1]:
                    unique_stops.append(st_name)

            self._json({
                "time": round(time_min),
                "distance": round(dist_km, 1),
                "fare": RouteFormatter.calculate_fare(dist_km),
                "stops": len(unique_stops),
                "interchanges": len(interchanges),
                "steps": steps
            })

    def _json(self, obj):
        data = json.dumps(obj).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *_):
        pass



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("0.0.0.0", port), Handler)
    print(f"Server running on port {port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
