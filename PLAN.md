# Plano de Arquitetura — OptimizeRoutesIntermediary + APIs

## Visão Geral

Transformar os scripts Python de reotimização CVRP em uma aplicação com **API REST** completa, pronta para consumo por um frontend. O projeto usa busca de vizinhança (2-opt*, realocação de pacotes) e OSRM para cálculo de distâncias.

---

## Estrutura de Diretórios Alvo

```
optimizeRoutesIntermediary/
├── src/
│   ├── classes/                    # (existente) tipos de dados
│   │   ├── types.py
│   │   ├── distances.py
│   │   ├── task1.py
│   │   └── exceptions.py
│   ├── services/                   # NOVO — lógica de negócio desacoplada
│   │   ├── __init__.py
│   │   ├── optimization_service.py # encapsula rotineIntermediary
│   │   ├── distance_service.py     # encapsula calculate_distance_matrix_m
│   │   └── solution_service.py     # serialização / comparação de soluções
│   ├── api/                        # NOVO — camada REST (FastAPI)
│   │   ├── __init__.py
│   │   ├── main.py                 # app FastAPI + lifespan
│   │   ├── dependencies.py         # injeção de dependências (OSRM config, Redis)
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── routes.py           # API 1 e API 4
│   │   │   ├── solutions.py        # API 2
│   │   │   ├── instances.py        # API 3
│   │   │   └── visualization.py    # API 5
│   │   └── schemas/
│   │       ├── __init__.py
│   │       ├── route_schemas.py    # OptimizeRequest, OptimizeResponse
│   │       └── solution_schemas.py # MetricsResponse, GeoJSONResponse
│   ├── (existente: twoopt.py, interRoute.py, operations.py, etc.)
│   └── ...
├── tests/                          # NOVO
│   ├── conftest.py
│   ├── test_optimization_service.py
│   └── test_api_routes.py
├── inputs/                         # (existente)
├── out/                            # (existente)
├── requirements.txt                # ATUALIZAR
├── .env.example                    # NOVO
├── docker-compose.yml              # NOVO
└── Dockerfile                      # NOVO
```

---

## Checklist de Implementação

### 🔧 Fase 1 — Preparação do Ambiente

- [ ] **1.1** Atualizar `requirements.txt` com as novas dependências:
  ```
  fastapi>=0.111.0
  uvicorn[standard]>=0.29.0
  pydantic>=2.7.0
  redis>=5.0.0
  celery>=5.4.0
  python-dotenv>=1.0.0
  pytest>=8.2.0
  httpx>=0.27.0
  ```
- [ ] **1.2** Criar `.env.example` com as variáveis de ambiente:
  ```env
  OSRM_HOST=http://localhost:5000
  REDIS_URL=redis://localhost:6379/0
  API_SECRET_KEY=changeme
  ```
- [ ] **1.3** Criar `docker-compose.yml` com os serviços:
  - `api` (FastAPI + Uvicorn)
  - `redis` (cache de soluções)
  - `osrm` (servidor de rotas self-hosted)
- [ ] **1.4** Criar `Dockerfile` para a aplicação Python

---

### 🏗️ Fase 2 — Camada de Serviços (`src/services/`)

- [ ] **2.1** Criar `src/services/__init__.py`
- [ ] **2.2** Criar `src/services/distance_service.py`
  - Mover lógica de `computeDistances.py` para um serviço injetável
  - Receber `OSRMConfig` via injeção em vez de hardcode
- [ ] **2.3** Criar `src/services/optimization_service.py`
  - Encapsular `rotineIntermediary` em uma classe `OptimizationService`
  - Expor método `optimize(instance, solution, config) -> CVRPSolution`
  - Expor método `optimize_dynamic(instance, num_lotes, config) -> Generator[CVRPSolution]`
- [ ] **2.4** Criar `src/services/solution_service.py`
  - `compare_methods(city, instance_name, methods) -> dict`
  - `to_geojson(solution) -> dict`
  - `calculate_metrics(solution, matrix_distance) -> dict`

---

### 📐 Fase 3 — Schemas Pydantic (`src/api/schemas/`)

- [ ] **3.1** Criar `src/api/schemas/route_schemas.py`
  ```python
  # Modelos de entrada e saída para as APIs de rota
  class PointSchema(BaseModel): lng: float; lat: float
  class DeliverySchema(BaseModel): id: str; point: PointSchema; size: int
  class CVRPInstanceSchema(BaseModel): name, origin, vehicle_capacity, deliveries
  class OptimizeRequest(BaseModel): instance, T, iterations, method
  class OptimizeResponse(BaseModel): solution_id, vehicles, total_distance, num_vehicles, time_s
  ```
- [ ] **3.2** Criar `src/api/schemas/solution_schemas.py`
  ```python
  class VehicleMetrics(BaseModel): vehicle_id, distance, occupation_pct, num_deliveries
  class MetricsResponse(BaseModel): solution_id, vehicles, total_distance, gain_pct
  class CompareEntry(BaseModel): method, total_distance, num_vehicles, time_s
  class GeoJSONResponse(BaseModel): type="FeatureCollection", features: list
  ```

---

### 🚀 Fase 4 — Endpoints da API (`src/api/routers/`)

- [ ] **4.1** Criar `src/api/main.py` — app FastAPI com lifespan (inicializa Redis, OSRM config)
- [ ] **4.2** Criar `src/api/dependencies.py` — `get_osrm_config()`, `get_redis()`, `get_optimization_service()`

#### API 1 — Otimização de Rotas On-demand
- [ ] **4.3** `POST /api/v1/routes/optimize`
  - Body: `OptimizeRequest` (instância CVRP + parâmetros)
  - Processa `rotineIntermediary` via `OptimizationService`
  - Salva resultado no Redis com `solution_id` (hash da instância + parâmetros)
  - Retorna: `OptimizeResponse` com rotas + métricas

#### API 2 — Métricas da Solução
- [ ] **4.4** `GET /api/v1/solutions/{solution_id}/metrics`
  - Recupera solução do Redis pelo ID
  - Calcula: distância por veículo, % ocupação de capacidade, ganho vs. solução inicial
  - Retorna: `MetricsResponse`

#### API 3 — Comparação de Métodos
- [ ] **4.5** `GET /api/v1/instances/{city}/solutions/compare?methods=kpmip,krs,krso`
  - Lê arquivos de saída em `out/{method}/{city}/`
  - Compara múltiplos métodos lado a lado
  - Retorna: lista de `CompareEntry`

#### API 4 — Simulação Dinâmica com Streaming
- [ ] **4.6** `POST /api/v1/routes/simulate-dynamic`
  - Body: instância + `num_lotes`
  - Usa `StreamingResponse` com `text/event-stream` (SSE)
  - A cada lote processado, envia um evento SSE com a solução parcial
  - Retorna: stream de `CVRPSolution` parciais em JSON

#### API 5 — Exportação GeoJSON
- [ ] **4.7** `GET /api/v1/routes/{solution_id}/geojson`
  - Recupera solução do Redis
  - Converte cada rota em `LineString` GeoJSON
  - Adiciona propriedades: `vehicle_id`, `color`, `occupation_pct`, `num_deliveries`
  - Retorna: `FeatureCollection` pronto para Mapbox / Leaflet / Google Maps

---

### 🧪 Fase 5 — Testes

- [ ] **5.1** Criar `tests/conftest.py` com fixtures usando instâncias reais de `inputs/pa-0/`
- [ ] **5.2** Criar `tests/test_optimization_service.py`
  - Testar `optimize()` com mock do OSRM
  - Verificar que solução retornada é válida (capacidade respeitada, todos pacotes atendidos)
- [ ] **5.3** Criar `tests/test_api_routes.py`
  - Testar todos os 5 endpoints com `TestClient` do FastAPI
  - Testar casos de erro (instância inválida, solution_id inexistente)

---

### 🐳 Fase 6 — Docker e Deploy

- [ ] **6.1** Finalizar `Dockerfile` com multi-stage build
- [ ] **6.2** Configurar `docker-compose.yml`:
  ```yaml
  services:
    api:      # FastAPI na porta 8000
    redis:    # Redis na porta 6379
    osrm:     # OSRM na porta 5000 (mapa OSM pré-processado)
  ```
- [ ] **6.3** Testar `docker compose up` e validar todos os endpoints

---

## Decisões Técnicas

| Componente     | Escolha              | Justificativa                                      |
|----------------|----------------------|----------------------------------------------------|
| Framework API  | **FastAPI**          | Async nativo, Swagger automático, Pydantic         |
| Validação      | **Pydantic v2**      | Já usa dataclasses similares no core               |
| Cache          | **Redis**            | Armazenar soluções por hash da instância           |
| Streaming      | **SSE (EventSource)**| Solução nativa HTTP, sem WebSocket overhead        |
| OSRM           | **Docker self-hosted**| Já usado no projeto, controle total da latência   |
| Containerização| **Docker Compose**   | API + Redis + OSRM em um único `docker compose up`|

---

## Ordem Recomendada de Execução

```
Fase 1 → Fase 2 → Fase 3 → Fase 4 (APIs 1→5) → Fase 5 → Fase 6
```

Cada fase é independente e pode ser commitada separadamente.
