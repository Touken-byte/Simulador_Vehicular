"""
Visualizacion interactiva del simulador de trafico sobre el grafo real
de calles de Yacuiba, usando Pygame.

Cubre: HU13 (visualizacion basica sobre el grafo), HU14 (colores por
velocidad/estado), y los controles de RF06-RF10 (iniciar, pausar,
reanudar, reiniciar, atras, velocidad de reproduccion).

Uso:
    python -m src.visualization.viewer

Controles durante la simulacion:
    ESPACIO : pausar / reanudar
    R       : reiniciar la simulacion
    ESC     : salir (volver a la terminal)
    + / -   : aumentar / disminuir la velocidad de reproduccion
"""
import sys
import yaml
import numpy as np
import networkx as nx
import osmnx as ox
import pygame

from src.agents.vehicle import generar_vehiculo

ANCHO, ALTO = 1000, 750
MARGEN = 40
COLOR_FONDO = (250, 250, 248)
COLOR_CALLE = (200, 210, 200)
COLOR_TEXTO = (30, 30, 30)
COLOR_PANEL = (30, 86, 49)      # verde oscuro (identidad Yacuiba)
COLOR_PANEL_TEXTO = (255, 255, 255)
COLOR_VEHICULO_LENTO = (200, 60, 60)     # rojo: vehiculo detenido/lento
COLOR_VEHICULO_MEDIO = (230, 170, 40)    # amarillo: velocidad media
COLOR_VEHICULO_RAPIDO = (60, 138, 70)    # verde: velocidad alta


def cargar_config(ruta_config="config.yaml"):
    with open(ruta_config, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def calcular_proyeccion(grafo):
    """Calcula la transformacion de coordenadas GPS (lat/lon) a pixeles de pantalla."""
    xs = [datos["x"] for _, datos in grafo.nodes(data=True)]
    ys = [datos["y"] for _, datos in grafo.nodes(data=True)]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    ancho_disponible = ANCHO - 2 * MARGEN
    alto_disponible = ALTO - 2 * MARGEN - 90  # deja espacio para el panel inferior

    def proyectar(lon, lat):
        px = MARGEN + (lon - min_x) / (max_x - min_x + 1e-9) * ancho_disponible
        py = MARGEN + (1 - (lat - min_y) / (max_y - min_y + 1e-9)) * alto_disponible
        return px, py

    return proyectar


class SimuladorVisual:
    def __init__(self, cfg):
        self.cfg = cfg
        self.grafo = ox.load_graphml(cfg["rutas"]["grafo_calles"])
        self.proyectar = calcular_proyeccion(self.grafo)

        self.pos_pantalla = {
            nodo: self.proyectar(datos["x"], datos["y"])
            for nodo, datos in self.grafo.nodes(data=True)
        }

        self.longitudes = {}
        for u, v, datos in self.grafo.edges(data=True):
            self.longitudes[(u, v)] = datos.get("length", 10.0)

        self.reiniciar()

    def reiniciar(self):
        sim_cfg = self.cfg["simulacion"]
        veh_cfg = self.cfg["vehiculo"]
        rng = np.random.default_rng(sim_cfg["semilla_aleatoria"])

        num_vehiculos_visual = min(sim_cfg["num_vehiculos"], 150)

        self.vehiculos = [
            generar_vehiculo(i, self.grafo, rng, velocidad_max_kmh=veh_cfg["velocidad_max_kmh"])
            for i in range(num_vehiculos_visual)
        ]
        self.tick_actual = 0
        self.pausado = False

    def _longitud_arista(self, u, v):
        if u == v:
            return 0.0
        return self.longitudes.get((u, v), self.longitudes.get((v, u), 10.0))

    def avanzar_tick(self, dt_seg=1.0):
        for vehiculo in self.vehiculos:
            if vehiculo.llego_al_destino():
                continue
            nodo_sig = vehiculo.nodo_siguiente()
            if nodo_sig is None:
                continue
            distancia_arista = self._longitud_arista(vehiculo.nodo_actual(), nodo_sig)
            avance_m = (vehiculo.velocidad_kmh * 1000 / 3600) * dt_seg
            vehiculo.distancia_en_arista_m += avance_m
            if vehiculo.distancia_en_arista_m >= distancia_arista:
                vehiculo.distancia_en_arista_m = 0.0
                vehiculo.posicion_idx += 1
        self.tick_actual += 1

    def posicion_pantalla_vehiculo(self, vehiculo):
        nodo_a = vehiculo.nodo_actual()
        nodo_b = vehiculo.nodo_siguiente()
        if nodo_b is None:
            return self.pos_pantalla[nodo_a]

        distancia_arista = max(self._longitud_arista(nodo_a, nodo_b), 1e-6)
        avance = min(vehiculo.distancia_en_arista_m / distancia_arista, 1.0)

        xa, ya = self.pos_pantalla[nodo_a]
        xb, yb = self.pos_pantalla[nodo_b]
        return (xa + (xb - xa) * avance, ya + (yb - ya) * avance)

    def color_por_velocidad(self, vehiculo):
        veh_cfg = self.cfg["vehiculo"]
        proporcion = vehiculo.velocidad_kmh / max(veh_cfg["velocidad_max_kmh"], 1)
        if proporcion < 0.4:
            return COLOR_VEHICULO_LENTO
        elif proporcion < 0.75:
            return COLOR_VEHICULO_MEDIO
        return COLOR_VEHICULO_RAPIDO


def _estilo_via(datos_arista):
    """Devuelve (color, grosor) segun el tipo de via de OpenStreetMap."""
    tipo = datos_arista.get("highway", "")
    if isinstance(tipo, list):
        tipo = tipo[0] if tipo else ""

    if tipo in ("primary", "trunk"):
        return (140, 140, 150), 5
    elif tipo == "secondary":
        return (165, 165, 175), 4
    elif tipo == "tertiary":
        return (185, 190, 185), 3
    elif tipo in ("residential", "unclassified"):
        return (205, 210, 205), 2
    else:
        return COLOR_CALLE, 1


def dibujar_calles(pantalla, sim):
    for u, v, datos in sim.grafo.edges(data=True):
        if u in sim.pos_pantalla and v in sim.pos_pantalla:
            color, grosor = _estilo_via(datos)
            pygame.draw.line(pantalla, color, sim.pos_pantalla[u], sim.pos_pantalla[v], grosor)

def dibujar_vehiculos(pantalla, sim):
    activos = 0
    for vehiculo in sim.vehiculos:
        if vehiculo.llego_al_destino():
            continue
        activos += 1
        x, y = sim.posicion_pantalla_vehiculo(vehiculo)
        color = sim.color_por_velocidad(vehiculo)
        pygame.draw.circle(pantalla, (255, 255, 255), (int(x), int(y)), 5)  # contorno blanco
        pygame.draw.circle(pantalla, color, (int(x), int(y)), 4)
    return activos

def dibujar_leyenda(pantalla, fuente):
    items = [
        (COLOR_VEHICULO_LENTO, "Lento"),
        (COLOR_VEHICULO_MEDIO, "Medio"),
        (COLOR_VEHICULO_RAPIDO, "Rapido"),
    ]
    x_inicio = ANCHO - 140
    y_inicio = 16
    fondo = pygame.Rect(x_inicio - 10, y_inicio - 8, 134, 8 + len(items) * 22)
    pygame.draw.rect(pantalla, (255, 255, 255), fondo, border_radius=6)
    pygame.draw.rect(pantalla, (210, 210, 210), fondo, 1, border_radius=6)
    for i, (color, etiqueta) in enumerate(items):
        cy = y_inicio + i * 22 + 6
        pygame.draw.circle(pantalla, color, (x_inicio, cy), 5)
        texto = fuente.render(etiqueta, True, COLOR_TEXTO)
        pantalla.blit(texto, (x_inicio + 14, cy - 8))

def dibujar_panel(pantalla, fuente, sim, velocidad_reproduccion, activos):
    rect_panel = pygame.Rect(0, ALTO - 80, ANCHO, 80)
    pygame.draw.rect(pantalla, COLOR_PANEL, rect_panel)

    estado = "PAUSADO" if sim.pausado else "EN CURSO"
    total = len(sim.vehiculos)
    llegados = total - activos

    lineas = [
        f"Simulador de Trafico Vehicular - Yacuiba, Bolivia   |   Estado: {estado}",
        f"Tick: {sim.tick_actual}   Vehiculos activos: {activos}/{total}   Llegados: {llegados}"
        f"   Velocidad: {velocidad_reproduccion}x",
        "[ESPACIO] Pausar/Reanudar   [R] Reiniciar   [+/-] Velocidad   [ESC] Salir",
    ]
    for i, linea in enumerate(lineas):
        texto = fuente.render(linea, True, COLOR_PANEL_TEXTO)
        pantalla.blit(texto, (16, ALTO - 74 + i * 22))


def main():
    cfg = cargar_config()

    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Simulador de Trafico Vehicular - Yacuiba, Bolivia")
    reloj = pygame.time.Clock()
    fuente = pygame.font.SysFont("dejavusansmono", 15)

    sim = SimuladorVisual(cfg)
    velocidad_reproduccion = 1
    ticks_por_frame_base = 1

    corriendo = True
    while corriendo:
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                corriendo = False
            elif evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    corriendo = False
                elif evento.key == pygame.K_SPACE:
                    sim.pausado = not sim.pausado
                elif evento.key == pygame.K_r:
                    sim.reiniciar()
                elif evento.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    velocidad_reproduccion = min(velocidad_reproduccion * 2, 16)
                elif evento.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    velocidad_reproduccion = max(velocidad_reproduccion // 2, 1)

        if not sim.pausado:
            for _ in range(ticks_por_frame_base * velocidad_reproduccion):
                sim.avanzar_tick()

        pantalla.fill(COLOR_FONDO)
        dibujar_calles(pantalla, sim)
        activos = dibujar_vehiculos(pantalla, sim)
        dibujar_panel(pantalla, fuente, sim, velocidad_reproduccion, activos)

        pygame.display.flip()
        reloj.tick(30)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
