# Simulador de Tráfico Vehicular Paralelo y Distribuido

Proyecto de la asignatura **TEL420 – Sistemas Paralelos**.
Simula tráfico vehicular sobre la red vial real de una zona de **Yacuiba, Bolivia**
(Plaza Principal – Mercado Central – Terminal de Buses), comparando rendimiento
entre ejecución secuencial, paralela en CPU y acelerada por GPU.

## Estado actual: Sprint 1 (entorno real + motor secuencial)

- [x] HU01 – Descarga del grafo real de calles (OSMnx)
- [x] HU02 – Identificación de intersecciones con semáforo
- [x] HU03 – Estructura del vehículo (agente)
- [x] HU04 – Lógica de movimiento y distancia de seguridad
- [x] HU05 – Generación de N vehículos con rutas aleatorias
- [x] HU06 – Simulación secuencial de control
- [ ] Sprint 2 – Paralelismo en CPU (OpenMP/multiproceso)
- [ ] Sprint 3 – Aceleración GPU (CUDA)
- [ ] Sprint 4 – Visualización
- [ ] Sprint 5 – Cierre y documentación

## Estructura del proyecto

```
Simulador_Vehicular/
├── config.yaml              # Parámetros de la zona y de la simulación
├── main.py                  # Punto de entrada (ejecuta la simulación)
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── data/                    # Grafo descargado (no se versiona en git)
├── output/                  # Métricas y gráficas generadas
└── src/
    ├── data/download_graph.py    # HU01, HU02
    ├── agents/vehicle.py         # HU03, HU05
    ├── simulation/engine.py      # HU04, HU06
    ├── parallel/                 # Sprint 2 (vacío por ahora)
    ├── gpu/                      # Sprint 3 (vacío por ahora)
    ├── visualization/            # Sprint 4 (vacío por ahora)
    └── metrics/                  # Utilidades de métricas y gráficas
```

## Opción A — Ejecución local (sin Docker)

```bash
# 1. Crear y activar un entorno virtual
python3 -m venv venv
source venv/bin/activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Descargar el grafo real de calles de Yacuiba (requiere internet)
python -m src.data.download_graph

# 4. Ejecutar la simulación secuencial
python main.py
```

Los resultados (tiempo de ejecución) quedan registrados en `output/metricas.csv`.

## Opción B — Ejecución con Docker

```bash
# 1. Construir la imagen
docker compose build

# 2. Descargar el grafo real (una sola vez, antes de simular)
docker compose run --rm simulador python -m src.data.download_graph

# 3. Ejecutar la simulación
docker compose up
```

Las carpetas `data/` y `output/` están montadas como volúmenes, así que los
resultados quedan disponibles también en tu máquina, fuera del contenedor.

## Nota importante sobre la descarga del grafo (HU01)

El script `src/data/download_graph.py` necesita conexión a internet real para
consultar los servidores de OpenStreetMap (Nominatim/Overpass). Ejecútalo
directamente en tu laptop (o dentro del contenedor Docker, que si tiene acceso
a internet de tu red). Si la consulta por nombre de lugar no delimita bien la
zona, el script cae automáticamente al *bounding box* de respaldo definido en
`config.yaml`.

## Próximos pasos

Una vez validado el Sprint 1 (grafo descargado + simulación secuencial
corriendo sin errores), seguimos con el Sprint 2: paralelización del cálculo
de posición de los vehículos usando multiproceso/OpenMP y medición de
speedup y eficiencia.
