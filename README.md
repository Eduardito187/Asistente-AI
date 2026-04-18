# Asistente AI Dismac

Asistente de compras para Dismac (retail boliviano de electrónica y electrodomésticos), con modelo de IA corriendo nativo en el equipo vía **Ollama + GPU**, base de datos propia **Postgres** alimentada por un **ingestor** que soporta **MySQL / REST / GraphQL / CSV** como fuentes, backend **FastAPI** (REST + GraphQL + chat) y frontend **Streamlit**. Todo en Docker Compose.

## Arquitectura

```
                     ┌────────────────┐
                     │   Frontend     │  Streamlit (chat es-BO)
                     │   :8501        │
                     └───────┬────────┘
                             │ HTTP
                     ┌───────▼────────┐       ┌──────────────┐
                     │   Backend      │──────▶│   Ollama     │
                     │   FastAPI      │  LLM  │  qwen2.5:7b  │
                     │  :8000         │◀──────│   :11434 GPU │
                     └───────┬────────┘       └──────────────┘
                             │ SQL
                     ┌───────▼────────┐
                     │   Postgres     │  BD propia (catálogo
                     │   :5432        │  espejo, sesiones, carrito)
                     └───────▲────────┘
                             │ upsert
                     ┌───────┴────────┐
                     │   Ingestor     │  adaptador seleccionable
                     └───────┬────────┘
            ┌────────────────┼────────────────────┐
            │                │                    │
     ┌──────▼─────┐  ┌───────▼──────┐      ┌──────▼──────┐
     │  MySQL     │  │  Mock API    │      │   CSV       │
     │ (Dismac    │  │ REST+GraphQL │      │  local      │
     │  ERP sim.) │  │  :8080       │      │             │
     └────────────┘  └──────────────┘      └─────────────┘
```

## Requisitos

- Docker + Docker Compose v2
- **GPU NVIDIA** + `nvidia-container-toolkit` configurado (si no tienes GPU, mirá la sección [Sin GPU](#sin-gpu))
- ~15 GB de disco libres (incluye modelo)

Verificado en: WSL2 Ubuntu 24.04, RTX 4060 Laptop 8 GB, 16 GB RAM.

## Puesta en marcha

```bash
cp .env.example .env
docker compose up -d --build
```

La primera vez tarda unos minutos porque:
1. Se construyen las imágenes.
2. `ollama-init` descarga el modelo `qwen2.5:7b-instruct-q4_K_M` (~4.7 GB).
3. MySQL semilla su catálogo y el ingestor hace la primera carga hacia Postgres.

Puntos de acceso:

| Servicio           | URL                                    |
|--------------------|----------------------------------------|
| Chat (Streamlit)   | <http://localhost:8501>                |
| Backend OpenAPI    | <http://localhost:8000/docs>           |
| Backend GraphQL    | <http://localhost:8000/graphql>        |
| Mock API Dismac    | <http://localhost:8080/productos>      |
| Mock API GraphQL   | <http://localhost:8080/graphql>        |
| Mock API CSV       | <http://localhost:8080/productos.csv>  |
| Ollama             | <http://localhost:11434>               |
| MySQL (origen)     | `localhost:3307`                       |
| Postgres (propio)  | `localhost:5432`                       |

## Cambiar la fuente del ingestor

Editar `.env` y reiniciar `ingestor`:

```bash
# Opciones: mysql | rest | graphql | csv
INGEST_SOURCE=rest
docker compose up -d ingestor
```

- `mysql` — lee del MySQL origen (simula la BD real de Dismac)
- `rest` — consume `INGEST_REST_URL` (default: mock API)
- `graphql` — consume `INGEST_GRAPHQL_URL` (default: mock API)
- `csv` — lee `INGEST_CSV_PATH` (montado desde `./ingestor/data/`)

Cuando la BD real de Dismac esté disponible, solo hay que:
1. Apuntar `MYSQL_HOST/USER/PASSWORD/DB` al origen real (o crear un nuevo adaptador si difiere el esquema).
2. O cambiar `INGEST_REST_URL` / `INGEST_GRAPHQL_URL` a la API real.

## Sin GPU

Editar `docker-compose.yml` y borrar el bloque `deploy.resources` del servicio `ollama`. El modelo seguirá funcionando sobre CPU pero mucho más lento. Alternativa: usar `llama3.2:3b` u otro modelo más liviano cambiando `OLLAMA_MODEL` en `.env`.

## Probar desde terminal

```bash
# REST: crear conversación nueva
curl -s -X POST http://localhost:8000/chat \
  -H 'content-type: application/json' \
  -d '{"mensaje": "Busco un televisor 4K de 55 pulgadas hasta Bs 5500"}' | jq

# GraphQL: listar productos
curl -s -X POST http://localhost:8000/graphql \
  -H 'content-type: application/json' \
  -d '{"query":"{ productos(q:\"laptop\") { sku nombre precioBob stock } }"}' | jq
```

## Estructura

```
.
├── docker-compose.yml
├── .env.example
├── db/               → init SQL de Postgres (catálogo, sesiones, carrito)
├── mysql-source/     → init SQL del MySQL origen (simula Dismac ERP)
├── mock-api/         → FastAPI + GraphQL sobre MySQL (simula API Dismac)
├── ingestor/         → sincroniza MySQL/REST/GraphQL/CSV → Postgres
│   └── adapters/     → un archivo por fuente
├── backend/          → FastAPI del asistente (chat, productos, carrito, GraphQL)
│   └── app/
│       ├── llm.py    → cliente Ollama + prompt boliviano
│       ├── rag.py    → recuperación híbrida sobre catálogo
│       └── routers/  → chat, productos, carrito
└── frontend/         → Streamlit (chat + buscador)
```

## Comandos útiles

```bash
# Ver logs de un servicio
docker compose logs -f backend

# Forzar reingesta manual
docker compose restart ingestor

# Entrar a Postgres
docker compose exec db psql -U asistente asistente_db

# Cambiar de modelo
# (editar OLLAMA_MODEL en .env, luego)
docker compose up -d ollama-init

# Apagar todo
docker compose down

# Apagar y borrar volúmenes (resetea BDs y modelo)
docker compose down -v
```
