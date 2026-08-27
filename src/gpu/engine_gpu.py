"""
Motor de simulacion acelerado por GPU usando CUDA (via Numba).

Estrategia: cada hilo de la GPU procesa un vehiculo independiente.
Se convierten los vehiculos a arrays planos de NumPy (posicion en la
arista, distancia de la arista actual, velocidad) porque CUDA no puede
operar directamente sobre objetos Python.

Cubre: HU09 (kernel CUDA) y HU10 (comparacion CPU vs GPU a gran escala).
"""
import time
import numpy as np
from numba import cuda


@cuda.jit
def _kernel_avanzar_vehiculos(distancia_en_arista, longitud_arista_actual,
                               velocidad_kmh, posicion_idx, num_aristas_ruta,
                               llego_destino, dt_seg):
    i = cuda.grid(1)
    if i >= distancia_en_arista.size:
        return
    if llego_destino[i]:
        return
    avance_m = (velocidad_kmh[i] * 1000.0 / 3600.0) * dt_seg
    distancia_en_arista[i] += avance_m
    if distancia_en_arista[i] >= longitud_arista_actual[i]:
        distancia_en_arista[i] = 0.0
        posicion_idx[i] += 1
        if posicion_idx[i] >= num_aristas_ruta[i]:
            llego_destino[i] = True


class MotorSimulacionGPU:
    def __init__(self, num_vehiculos, duracion_ticks, velocidad_max_kmh,
                 velocidad_min_kmh=5, longitud_arista_prom_m=80.0,
                 semilla_aleatoria=42):
        self.num_vehiculos = num_vehiculos
        self.duracion_ticks = duracion_ticks
        rng = np.random.default_rng(semilla_aleatoria)

        self.velocidad_kmh = rng.uniform(
            velocidad_min_kmh, velocidad_max_kmh, size=num_vehiculos
        ).astype(np.float32)
        self.distancia_en_arista = np.zeros(num_vehiculos, dtype=np.float32)
        self.posicion_idx = np.zeros(num_vehiculos, dtype=np.int32)
        self.num_aristas_ruta = rng.integers(5, 40, size=num_vehiculos).astype(np.int32)
        self.llego_destino = np.zeros(num_vehiculos, dtype=np.bool_)
        self.longitud_arista_actual = np.full(
            num_vehiculos, longitud_arista_prom_m, dtype=np.float32
        )

    def ejecutar(self):
        inicio = time.perf_counter()

        d_distancia = cuda.to_device(self.distancia_en_arista)
        d_longitud = cuda.to_device(self.longitud_arista_actual)
        d_velocidad = cuda.to_device(self.velocidad_kmh)
        d_posicion = cuda.to_device(self.posicion_idx)
        d_num_aristas = cuda.to_device(self.num_aristas_ruta)
        d_llego = cuda.to_device(self.llego_destino)

        hilos_por_bloque = 256
        bloques_por_grid = (self.num_vehiculos + (hilos_por_bloque - 1)) // hilos_por_bloque

        for _tick in range(self.duracion_ticks):
            _kernel_avanzar_vehiculos[bloques_por_grid, hilos_por_bloque](
                d_distancia, d_longitud, d_velocidad, d_posicion,
                d_num_aristas, d_llego, 1.0
            )

        cuda.synchronize()

        self.posicion_idx = d_posicion.copy_to_host()
        self.llego_destino = d_llego.copy_to_host()

        fin = time.perf_counter()
        tiempo_total_seg = fin - inicio

        return {
            "modo": "gpu_cuda",
            "num_vehiculos": self.num_vehiculos,
            "duracion_ticks": self.duracion_ticks,
            "tiempo_total_seg": tiempo_total_seg,
        }
