"""
Benchmark comparativo: secuencial vs. paralelo en CPU con distinta
cantidad de procesos. Calcula speedup y eficiencia.

Cubre: HU08 y una primera versión de HU12 (gráficas comparativas).

Uso:
    python -m src.metrics.benchmark
"""
import os
import csv
import multiprocessing as mp
import yaml
import osmnx as ox
import matplotlib.pyplot as plt

from src.simulation.engine import MotorSimulacion
from src.parallel.engine_parallel import MotorSimulacionParalelo


def cargar_config(ruta_config="config.yaml"):
    with open(ruta_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def correr_benchmark():
    cfg = cargar_config()
    grafo = ox.load_graphml(cfg["rutas"]["grafo_calles"])
    sim_cfg = cfg["simulacion"]
    veh_cfg = cfg["vehiculo"]

    resultados = []

    print("Ejecutando modo SECUENCIAL (línea base)...")
    motor_sec = MotorSimulacion(
        grafo=grafo,
        num_vehiculos=sim_cfg["num_vehiculos"],
        duracion_ticks=sim_cfg["duracion_ticks"],
        velocidad_max_kmh=veh_cfg["velocidad_max_kmh"],
        distancia_seguridad_m=veh_cfg["distancia_seguridad_m"],
        semilla_aleatoria=sim_cfg["semilla_aleatoria"],
    )
    r_sec = motor_sec.ejecutar()
    tiempo_base = r_sec["tiempo_total_seg"]
    r_sec.update({"num_procesos": 1, "speedup": 1.0, "eficiencia": 1.0})
    resultados.append(r_sec)
    print(f"  Tiempo secuencial: {tiempo_base:.4f} s")

    max_cpus = mp.cpu_count()
    niveles = sorted(set(n for n in [2, 4, max_cpus] if n <= max_cpus))
    print(f"CPUs detectadas en esta máquina: {max_cpus}")

    for n_proc in niveles:
        print(f"Ejecutando modo PARALELO con {n_proc} procesos...")
        motor_par = MotorSimulacionParalelo(
            grafo=grafo,
            num_vehiculos=sim_cfg["num_vehiculos"],
            duracion_ticks=sim_cfg["duracion_ticks"],
            velocidad_max_kmh=veh_cfg["velocidad_max_kmh"],
            distancia_seguridad_m=veh_cfg["distancia_seguridad_m"],
            semilla_aleatoria=sim_cfg["semilla_aleatoria"],
            num_procesos=n_proc,
        )
        r_par = motor_par.ejecutar()
        speedup = tiempo_base / r_par["tiempo_total_seg"]
        eficiencia = speedup / n_proc
        r_par.update({"speedup": speedup, "eficiencia": eficiencia})
        resultados.append(r_par)
        print(f"  Tiempo: {r_par['tiempo_total_seg']:.4f} s | "
              f"Speedup: {speedup:.2f}x | Eficiencia: {eficiencia:.2f}")

    return resultados


def guardar_resultados(resultados, carpeta_salida="output/"):
    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_csv = os.path.join(carpeta_salida, "benchmark_sprint2.csv")
    campos = ["modo", "num_vehiculos", "duracion_ticks", "num_procesos",
              "tiempo_total_seg", "speedup", "eficiencia"]
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resultados:
            writer.writerow({k: r.get(k, "") for k in campos})
    print(f"Resultados guardados en: {ruta_csv}")


def graficar(resultados, carpeta_salida="output/"):
    procesos = [r["num_procesos"] for r in resultados]
    speedups = [r["speedup"] for r in resultados]
    eficiencias = [r["eficiencia"] for r in resultados]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))

    ax1.plot(procesos, speedups, marker="o", color="#3C8A46", label="Speedup real")
    ax1.plot(procesos, procesos, linestyle="--", color="gray", label="Speedup ideal")
    ax1.set_xlabel("Número de procesos")
    ax1.set_ylabel("Speedup")
    ax1.set_title("Speedup vs. número de procesos")
    ax1.legend()
    ax1.grid(alpha=0.3)

    ax2.plot(procesos, eficiencias, marker="o", color="#1E5631")
    ax2.axhline(1.0, linestyle="--", color="gray")
    ax2.set_xlabel("Número de procesos")
    ax2.set_ylabel("Eficiencia")
    ax2.set_title("Eficiencia vs. número de procesos")
    ax2.grid(alpha=0.3)

    plt.tight_layout()
    ruta_png = os.path.join(carpeta_salida, "benchmark_sprint2.png")
    plt.savefig(ruta_png, dpi=150)
    print(f"Gráfica guardada en: {ruta_png}")


if __name__ == "__main__":
    resultados = correr_benchmark()
    guardar_resultados(resultados)
    graficar(resultados)
