"""
Define la estructura de un vehículo (agente) dentro de la simulación.

Cubre: HU03 (estructura del vehículo).
"""
from dataclasses import dataclass, field
import networkx as nx


@dataclass
class Vehiculo:
    id: int
    ruta: list          # lista de nodos del grafo que el vehículo debe recorrer
    velocidad_kmh: float
    velocidad_max_kmh: float
    posicion_idx: int = 0       # índice actual dentro de la ruta
    distancia_en_arista_m: float = 0.0  # avance dentro de la arista actual
    detenido: bool = False

    def nodo_actual(self):
        return self.ruta[self.posicion_idx]

    def nodo_siguiente(self):
        if self.posicion_idx + 1 < len(self.ruta):
            return self.ruta[self.posicion_idx + 1]
        return None

    def llego_al_destino(self):
        return self.posicion_idx >= len(self.ruta) - 1


def generar_vehiculo(id_vehiculo, grafo, rng, velocidad_max_kmh=40, velocidad_min_kmh=5):
    """
    Genera un vehículo con una ruta aleatoria válida dentro del grafo real.
    Cubre HU05 (generación de N vehículos con rutas aleatorias).
    """
    nodos = list(grafo.nodes)
    origen = rng.choice(nodos)
    destino = rng.choice(nodos)

    intentos = 0
    ruta = None
    while intentos < 10:
        try:
            ruta = nx.shortest_path(grafo, origen, destino, weight="length")
            if len(ruta) >= 2:
                break
        except nx.NetworkXNoPath:
            destino = rng.choice(nodos)
        intentos += 1

    if ruta is None or len(ruta) < 2:
        # Como último recurso, la ruta es un único nodo (el vehículo no se mueve).
        ruta = [origen]

    velocidad_inicial = rng.uniform(velocidad_min_kmh, velocidad_max_kmh)

    return Vehiculo(
        id=id_vehiculo,
        ruta=ruta,
        velocidad_kmh=velocidad_inicial,
        velocidad_max_kmh=velocidad_max_kmh,
    )
