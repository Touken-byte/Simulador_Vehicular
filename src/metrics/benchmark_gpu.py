"""
Benchmark comparativo: CPU secuencial vs. GPU (CUDA) con distintas
cantidades de vehiculos, para demostrar escalabilidad.

Cubre: HU10 y una version ampliada de HU12 (graficas comparativas).
"""
import os
import csv
import time
import numpy as np
import matplotlib.pyplot as plt

from src.gpu.engine_gpu import MotorSimulacionGPU


def _cpu_referencia(num_vehiculos, duracion_ticks, velocidad_max_kmh=40,
                     velocidad_min_kmh=5, longitud_arista_prom_m=80.0,
                     semilla_aleatoria=42):
    rng = np.random.default_rng(semilla_aleatoria)
    velocidad_kmh = rng.uniform(velocidad_min_kmh, velocidad_max_kmh, size=num_vehiculos)
    distancia_en_arista = np.zeros(num_vehiculos)
    posicion_idx = np.zeros(num_vehiculos, dtype=np.int32)
    num_aristas_ruta = rng.integers(5, 40, size=num_vehiculos)
    llego_destino = np.zeros(num_vehiculos, dtype=bool)
    longitud_arista_actual = np.full(num_vehiculos, longitud_arista_prom_m)

    inicio = time.perf_counter()
    for _tick in range(duracion_ticks):
        activos = ~llego_destino
        avance_m = (velocidad_kmh[activos] * 1000.0 / 3600.0) * 1.0
        distancia_en_arista[activos] += avance_m
        cruzan = np.zeros_like(activos)
        cruzan[activos] = distancia_en_arista[activos] >= longitud_arista_actual[activos]
        distancia_en_arista[cruzan] = 0.0
        posicion_idx[cruzan] += 1
        llego_destino[cruzan & (posicion_idx >= num_aristas_ruta)] = True
    fin = time.perf_counter()

    return {"modo": "cpu_vectorizado", "num_vehiculos": num_vehiculos,
            "duracion_ticks": duracion_ticks, "tiempo_total_seg": fin - inicio}


def correr_benchmark():
    duracion_ticks = 500
    niveles_vehiculos = [1000, 10000, 50000, 100000, 500000]
    resultados = []

    for n in niveles_vehiculos:
        print(f"--- {n} vehiculos ---")
        r_cpu = _cpu_referencia(n, duracion_ticks)
        print(f"  CPU (vectorizado numpy): {r_cpu['tiempo_total_seg']:.4f} s")
        resultados.append(r_cpu)

        motor_gpu = MotorSimulacionGPU(
            num_vehiculos=n, duracion_ticks=duracion_ticks, velocidad_max_kmh=40
        )
        r_gpu = motor_gpu.ejecutar()
        speedup = r_cpu["tiempo_total_seg"] / r_gpu["tiempo_total_seg"]
        r_gpu["speedup_vs_cpu"] = speedup
        print(f"  GPU (CUDA): {r_gpu['tiempo_total_seg']:.4f} s | Speedup: {speedup:.2f}x")
        resultados.append(r_gpu)

    return resultados


def guardar_y_graficar(resultados, carpeta_salida="output/"):
    os.makedirs(carpeta_salida, exist_ok=True)
    ruta_csv = os.path.join(carpeta_salida, "benchmark_sprint3_gpu.csv")
    campos = ["modo", "num_vehiculos", "duracion_ticks", "tiempo_total_seg", "speedup_vs_cpu"]
    with open(ruta_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        for r in resultados:
            writer.writerow({k: r.get(k, "") for k in campos})
    print(f"Resultados guardados en: {ruta_csv}")

    niveles = sorted(set(r["num_vehiculos"] for r in resultados))
    t_cpu = [next(r["tiempo_total_seg"] for r in resultados
                  if r["num_vehiculos"] == n and r["modo"] == "cpu_vectorizado") for n in niveles]
    t_gpu = [next(r["tiempo_total_seg"] for r in resultados
                  if r["num_vehiculos"] == n and r["modo"] == "gpu_cuda") for n in niveles]

    plt.figure(figsize=(8, 5))
    plt.plot(niveles, t_cpu, marker="o", color="#3C8A46", label="CPU (vectorizado)")
    plt.plot(niveles, t_gpu, marker="o", color="#1E5631", label="GPU (CUDA)")
    plt.xscale("log")
    plt.yscale("log")
    plt.xlabel("Numero de vehiculos (escala log)")
    plt.ylabel("Tiempo de ejecucion (s, escala log)")
    plt.title("CPU vs GPU: tiempo de ejecucion vs escala")
    plt.legend()
    plt.grid(alpha=0.3, which="both")
    ruta_png = os.path.join(carpeta_salida, "benchmark_sprint3_gpu.png")
    plt.tight_layout()
    plt.savefig(ruta_png, dpi=150)
    print(f"Grafica guardada en: {ruta_png}")


if __name__ == "__main__":
    resultados = correr_benchmark()
    guardar_y_graficar(resultados)
