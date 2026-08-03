"""
Punto de entrada principal del Simulador de Tráfico Vehicular.

Sprint 1: ejecuta únicamente el modo secuencial (versión de control).
Los modos 'cpu_paralelo' y 'gpu' se habilitarán en los Sprints 2 y 3.

Uso:
    python main.py
"""
import os
import csv
import yaml
import osmnx as ox

from src.simulation.engine import MotorSimulacion


def cargar_config(ruta_config="config.yaml"):
    with open(ruta_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def registrar_metricas(resultado, carpeta_salida="output/"):
    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_csv = os.path.join(carpeta_salida, "metricas.csv")

    existe = os.path.isfile(ruta_csv)
    with open(ruta_csv, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(resultado.keys()))
        if not existe:
            writer.writeheader()
        writer.writerow(resultado)

    print(f"Métricas registradas en: {ruta_csv}")


def main():
    cfg = cargar_config()

    ruta_grafo = cfg["rutas"]["grafo_calles"]
    if not os.path.isfile(ruta_grafo):
        raise FileNotFoundError(
            f"No se encontró el grafo en '{ruta_grafo}'. "
            "Ejecuta primero: python -m src.data.download_graph"
        )

    print(f"Cargando grafo de calles desde: {ruta_grafo} ...")
    grafo = ox.load_graphml(ruta_grafo)
    print(f"Grafo cargado: {len(grafo.nodes)} nodos, {len(grafo.edges)} aristas.")

    sim_cfg = cfg["simulacion"]
    veh_cfg = cfg["vehiculo"]

    motor = MotorSimulacion(
        grafo=grafo,
        num_vehiculos=sim_cfg["num_vehiculos"],
        duracion_ticks=sim_cfg["duracion_ticks"],
        velocidad_max_kmh=veh_cfg["velocidad_max_kmh"],
        distancia_seguridad_m=veh_cfg["distancia_seguridad_m"],
        semilla_aleatoria=sim_cfg["semilla_aleatoria"],
    )

    print(f"Ejecutando simulación secuencial con {sim_cfg['num_vehiculos']} vehículos "
          f"durante {sim_cfg['duracion_ticks']} ticks...")
    resultado = motor.ejecutar()

    print(f"Tiempo total de ejecución: {resultado['tiempo_total_seg']:.4f} segundos")
    registrar_metricas(resultado, cfg["rutas"]["resultados"])


if __name__ == "__main__":
    main()
