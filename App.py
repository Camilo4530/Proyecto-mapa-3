from flask import Flask, request, jsonify
import osmnx as ox
import networkx as nx
import pickle
import os

app = Flask(__name__)

# -----------------------
# Carga o crea el grafo
# -----------------------
def cargar_grafo():
    if os.path.exists("bogota_graph.pkl"):
        with open("bogota_graph.pkl", "rb") as f:
            print("✅ Grafo cargado desde archivo.")
            return pickle.load(f)
    else:
        print("⏳ Descargando grafo de Bogotá...")
        G = ox.graph_from_place("Bogotá, Colombia", network_type="all")
        with open("bogota_graph.pkl", "wb") as f:
            pickle.dump(G, f)
        print("✅ Grafo descargado y guardado.")
        return G

G = cargar_grafo()

# ------------------------
# Ruta para calcular camino
# ------------------------
@app.route("/camino", methods=["POST"])
def calcular_camino():
    data = request.json
    nodos = data.get("nodos", [])

    if len(nodos) < 2:
        return jsonify({"error": "Se necesitan al menos dos nodos"}), 400

    try:
        # Encuentra el nodo más cercano en el grafo para cada punto
        nodos_grafo = [
            ox.distance.nearest_nodes(G, lon=float(n["lng"]), lat=float(n["lat"]))
            for n in nodos
        ]

        print("🔍 Nodos más cercanos en el grafo:", nodos_grafo)

        camino_total = []

        for i in range(len(nodos_grafo) - 1):
            try:
                subcamino = nx.shortest_path(
                    G,
                    nodos_grafo[i],
                    nodos_grafo[i + 1],
                    weight="length"
                )
                camino_total.extend(subcamino[:-1])
            except Exception as e:
                print(f"⚠️ No hay camino entre {nodos_grafo[i]} y {nodos_grafo[i + 1]}: {e}")
                return jsonify({"camino": [], "mensaje": "No hay camino disponible"}), 200

        # Añadir el último nodo
        camino_total.append(nodos_grafo[-1])

        # Obtener coordenadas de los nodos del camino
        coordenadas = [
            {"lat": G.nodes[n]["y"], "lng": G.nodes[n]["x"]} for n in camino_total
        ]

        print("✅ Camino encontrado.")
        return jsonify({"camino": coordenadas, "mensaje": "Camino encontrado"}), 200

    except Exception as e:
        print("❌ Error general:", e)
        return jsonify({"error": "Error interno"}), 500


if __name__ == "__main__":
    app.run(debug=True)













