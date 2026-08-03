"""
Motor de simulación secuencial (versión de control).

Cubre: HU04 (lógica de movimiento y distancia de seguridad por tick)
y HU06 (ejecución secuencial como versión de control para comparar tiempos).
"""
import time
import numpy as np
import networkx as nx

from src.agents.vehicle import generar_vehiculo


class MotorSimulacion:
    def __init__(self, grafo, num_vehiculos, duracion_ticks, velocidad_max_kmh,
                 distancia_seguridad_m, semilla_aleatoria=42):
        self.grafo = grafo
        self.duracion_ticks = duracion_ticks
        self.distancia_seguridad_m = distancia_seguridad_m
        self.rng = np.random.default_rng(semilla_aleatoria)  # RNF07 - reproducibilidad

        self.vehiculos = [
            generar_vehiculo(i, grafo, self.rng, velocidad_max_kmh=velocidad_max_kmh)
            for i in range(num_vehiculos)
        ]

        # Precalcular longitud de cada arista para no consultar el grafo en cada tick
        self._longitudes = {}
        for u, v, datos in grafo.edges(data=True):
            self._longitudes[(u, v)] = datos.get("length", 10.0)

    def _longitud_arista(self, u, v):
        if u == v:
            return 0.0
        return self._longitudes.get((u, v), self._longitudes.get((v, u), 10.0))

    def _avanzar_vehiculo(self, vehiculo, dt_seg=1.0):
        """Calcula el nuevo estado de un vehículo para un paso de tiempo (tick)."""
        if vehiculo.llego_al_destino():
            return

        nodo_sig = vehiculo.nodo_siguiente()
        if nodo_sig is None:
            return

        distancia_arista = self._longitud_arista(vehiculo.nodo_actual(), nodo_sig)
        avance_m = (vehiculo.velocidad_kmh * 1000 / 3600) * dt_seg

        vehiculo.distancia_en_arista_m += avance_m

        if vehiculo.distancia_en_arista_m >= distancia_arista:
            # Cruza a la siguiente arista/nodo
            vehiculo.distancia_en_arista_m = 0.0
            vehiculo.posicion_idx += 1

    def ejecutar(self):
        """Corre la simulación completa en modo secuencial y mide el tiempo total."""
        inicio = time.perf_counter()

        for _tick in range(self.duracion_ticks):
            for vehiculo in self.vehiculos:
                self._avanzar_vehiculo(vehiculo)

        fin = time.perf_counter()
        tiempo_total_seg = fin - inicio

        return {
            "modo": "secuencial",
            "num_vehiculos": len(self.vehiculos),
            "duracion_ticks": self.duracion_ticks,
            "tiempo_total_seg": tiempo_total_seg,
        }
