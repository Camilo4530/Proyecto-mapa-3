from flask import Flask, request, jsonify, render_template
from flasgger import Swagger
import osmnx as ox
import networkx as nx
import pickle
import os

app = Flask(__name__)
swagger = Swagger(app)

@app.route('/get_address')
def get_address():
    """
    🔎 Obtener dirección desde coordenadas
    ---
    tags:
      - Geocodificación Inversa
    summary: Traduce coordenadas GPS a una dirección humana
    description: |
      Este endpoint convierte una **latitud** y **longitud** en una dirección postal legible.  
      Ideal para aplicaciones que trabajan con mapas o ubicaciones en tiempo real.

      Actualmente devuelve una dirección simulada, pero puede integrarse fácilmente con servicios como:
      - Nominatim (OpenStreetMap)
      - Google Maps Geocoding API
      - Mapbox Geocoding API

      📍 Ejemplo de uso:

      ```
      /get_address?lat=4.7110&lng=-74.0721
      ```

      🔁 Útil para:
      - Interfaces de usuario que muestran ubicaciones
      - Seguimiento en tiempo real
      - Verificación de zonas geográficas
    parameters:
      - name: lat
        in: query
        type: number
        required: true
        description: Coordenada de latitud en formato decimal
        example: 4.7110
      - name: lng
        in: query
        type: number
        required: true
        description: Coordenada de longitud en formato decimal
        example: -74.0721
    responses:
      200:
        description: Dirección obtenida exitosamente
        schema:
          type: object
          properties:
            address:
              type: string
              description: Dirección simulada devuelta por el sistema
              example: "Calle 26 # 13-40, Bogotá, Colombia"
      400:
        description: Faltan parámetros obligatorios
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Faltan parámetros"
    """
    lat = request.args.get('lat')
    lng = request.args.get('lng')
    if not lat or not lng:
        return jsonify({'error': 'Faltan parámetros'}), 400

    direccion = f"Dirección simulada para lat={lat}, lng={lng}"
    return jsonify({'address': direccion})

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

@app.route("/camino", methods=["POST"])
def calcular_camino():
    """
    Calcular el camino más corto entre varios nodos dados
    ---
    tags:
      - Rutas
    consumes:
      - application/json
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - nodos
          properties:
            nodos:
              type: array
              description: Lista de puntos con latitud y longitud
              items:
                type: object
                required:
                  - lat
                  - lng
                properties:
                  lat:
                    type: number
                    description: Latitud del nodo
                    example: 4.60971
                  lng:
                    type: number
                    description: Longitud del nodo
                    example: -74.08175
    responses:
      200:
        description: Camino encontrado exitosamente
        schema:
          type: object
          properties:
            camino:
              type: array
              description: Lista de coordenadas del camino más corto
              items:
                type: object
                properties:
                  lat:
                    type: number
                    description: Latitud del punto
                  lng:
                    type: number
                    description: Longitud del punto
            mensaje:
              type: string
              example: "Camino encontrado"
      400:
        description: Error en la solicitud
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Se necesitan al menos dos nodos"
            mensaje:
              type: string
              example: "No hay camino disponible"
      500:
        description: Error interno del servidor
        schema:
          type: object
          properties:
            error:
              type: string
              example: "Error interno"
    """
    data = request.json
    nodos = data.get("nodos", [])

    if len(nodos) < 2:
        return jsonify({"error": "Se necesitan al menos dos nodos"}), 400

    try:
        nodos_grafo = [
            ox.distance.nearest_nodes(
                G,
                float(n["lng"]),
                float(n["lat"])
            )
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
                return jsonify({"camino": [], "mensaje": "No hay camino disponible"}), 400

        camino_total.append(nodos_grafo[-1])

        coordenadas = [
            {"lat": G.nodes[n]["y"], "lng": G.nodes[n]["x"]} for n in camino_total
        ]

        print("✅ Camino encontrado.")
        return jsonify({"camino": coordenadas, "mensaje": "Camino encontrado"}), 200

    except Exception as e:
        print("❌ Error general:", e)
        return jsonify({"error": "Error interno"}), 500

@app.route("/", methods=["GET"])
def mostrar_mapa():
    """
    Página principal con el mapa interactivo
    ---
    tags:
      - Interfaz
    responses:
      200:
        description: Página HTML del mapa
    """
    return render_template("mapa.html")

if __name__ == "__main__":
    print("\n🚀 Servidor iniciado. Accede a:")
    print(" - Mapa: http://127.0.0.1:5000/")
    print(" - Documentación Swagger: http://127.0.0.1:5000/apidocs/\n")
    app.run(debug=True)
















