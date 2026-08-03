"""
Motor de simulación paralelo en CPU usando multiprocessing.

Estrategia: paralelismo de datos "grueso". Se divide el conjunto de
vehículos en lotes y cada proceso simula su lote completo (todos los
ticks) de forma independiente, ya que en este modelo los vehículos no
interactúan entre sí. Esto evita el overhead de comunicación que tendría
sincronizar tick por tick entre procesos.

Cubre: HU07 (paralelización con multiproceso) y HU08 (medición de
speedup/eficiencia con distinta cantidad de procesos).
"""
import time
import multiprocessing as mp
import numpy as np

from src.agents.vehicle import generar_vehiculo


def _simular_lote(vehiculos_lote, longitudes, duracion_ticks, dt_seg=1.0):
    """Corre la simulación completa (todos los ticks) sobre un lote de vehículos."""

    def longitud_arista(u, v):
        if u == v:
            return 0.0
        return longitudes.get((u, v), longitudes.get((v, u), 10.0))

    for _tick in range(duracion_ticks):
        for vehiculo in vehiculos_lote:
            if vehiculo.llego_al_destino():
                continue
            nodo_sig = vehiculo.nodo_siguiente()
            if nodo_sig is None:
                continue
            distancia_arista = longitud_arista(vehiculo.nodo_actual(), nodo_sig)
            avance_m = (vehiculo.velocidad_kmh * 1000 / 3600) * dt_seg
            vehiculo.distancia_en_arista_m += avance_m
            if vehiculo.distancia_en_arista_m >= distancia_arista:
                vehiculo.distancia_en_arista_m = 0.0
                vehiculo.posicion_idx += 1

    return vehiculos_lote


class MotorSimulacionParalelo:
    def __init__(self, grafo, num_vehiculos, duracion_ticks, velocidad_max_kmh,
                 distancia_seguridad_m, semilla_aleatoria=42, num_procesos=None):
        self.grafo = grafo
        self.duracion_ticks = duracion_ticks
        self.num_procesos = num_procesos or mp.cpu_count()
        self.rng = np.random.default_rng(semilla_aleatoria)

        self.vehiculos = [
            generar_vehiculo(i, grafo, self.rng, velocidad_max_kmh=velocidad_max_kmh)
            for i in range(num_vehiculos)
        ]

        self._longitudes = {}
        for u, v, datos in grafo.edges(data=True):
            self._longitudes[(u, v)] = datos.get("length", 10.0)

    def _dividir_en_lotes(self):
        n = self.num_procesos
        return [self.vehiculos[i::n] for i in range(n)]

    def ejecutar(self):
        inicio = time.perf_counter()

        lotes = self._dividir_en_lotes()
        args = [(lote, self._longitudes, self.duracion_ticks) for lote in lotes]

        with mp.Pool(processes=self.num_procesos) as pool:
            resultados_lotes = pool.starmap(_simular_lote, args)

        self.vehiculos = [v for lote in resultados_lotes for v in lote]

        fin = time.perf_counter()
        tiempo_total_seg = fin - inicio

        return {
            "modo": f"cpu_paralelo_{self.num_procesos}proc",
            "num_vehiculos": len(self.vehiculos),
            "duracion_ticks": self.duracion_ticks,
            "num_procesos": self.num_procesos,
            "tiempo_total_seg": tiempo_total_seg,
        }
