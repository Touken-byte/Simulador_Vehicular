"""
Descarga el grafo real de calles de la zona de estudio (Yacuiba, Bolivia)
usando OpenStreetMap a través de OSMnx.

Cubre: HU01 (grafo real de calles) y HU02 (identificación de intersecciones
con semáforo / prioridad).

Uso:
    python -m src.data.download_graph
"""
import os
import yaml
import networkx as nx
import osmnx as ox
import pandas as pd


def cargar_config(ruta_config="config.yaml"):
    with open(ruta_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def descargar_grafo(cfg):
    zona = cfg["zona"]
    red_vial = zona.get("red_vial", "drive")

    grafo = None

    # 1) Intento principal: por nombre de lugar (más preciso si Nominatim
    #    reconoce bien los límites de Yacuiba).
    try:
        print(f"Intentando descargar por nombre de lugar: {zona['place_query']} ...")
        grafo = ox.graph_from_place(zona["place_query"], network_type=red_vial)
    except Exception as e:
        print(f"No se pudo descargar por nombre de lugar ({e}).")
        print("Usando bounding box de respaldo...")

    # 2) Respaldo: bounding box manual sobre la zona Plaza-Mercado-Terminal.
    if grafo is None:
        bbox = zona["bbox"]
        grafo = ox.graph_from_bbox(
            bbox["north"], bbox["south"], bbox["east"], bbox["west"],
            network_type=red_vial,
        )

    return grafo


def identificar_semaforos(grafo):
    """Extrae los nodos marcados como semáforo (highway=traffic_signals) en OSM."""
    nodos, _ = ox.graph_to_gdfs(grafo)
    if "highway" in nodos.columns:
        semaforos = nodos[nodos["highway"] == "traffic_signals"]
    else:
        semaforos = nodos.iloc[0:0]  # dataframe vacío con las mismas columnas
    print(f"Intersecciones con semáforo detectadas: {len(semaforos)}")
    return semaforos


def main():
    cfg = cargar_config()
    os.makedirs("data", exist_ok=True)

    grafo = descargar_grafo(cfg)
    print(f"Grafo descargado: {len(grafo.nodes)} nodos, {len(grafo.edges)} aristas.")

    ruta_grafo = cfg["rutas"]["grafo_calles"]
    ox.save_graphml(grafo, ruta_grafo)
    print(f"Grafo guardado en: {ruta_grafo}")

    semaforos = identificar_semaforos(grafo)
    ruta_semaforos = "data/interseccion_semaforos.csv"
    semaforos.to_csv(ruta_semaforos)
    print(f"Intersecciones con semáforo guardadas en: {ruta_semaforos}")


if __name__ == "__main__":
    main()
