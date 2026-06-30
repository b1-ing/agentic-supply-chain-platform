import osmnx as ox

# ---- 1. ADD THIS NEW IMPORT ----
import folium_plots


def create_interactive_map():
    print("[*] Loading your map graph...")
    graph = ox.load_graphml("cache/singapore.graphml")

    print("[*] Generating interactive leaflet map...")
    # ---- 2. CHANGE ox.plot_graph_folium TO folium.plot_graph ----
    graph_map = folium_plots.plot_graph_folium(
        graph,
        tiles="openstreetmap",  # Background map style
        color="blue",  # Color of the roads
        edge_width=2,
        node_size=3,
    )

    # Save it as an HTML file
    output_html = "singapore_visualization.html"
    graph_map.save(output_html)
    print(f"[+] Done! Open '{output_html}' in any web browser to explore it.")


if __name__ == "__main__":
    create_interactive_map()
