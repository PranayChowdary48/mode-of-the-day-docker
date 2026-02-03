# Mood of the Day — Docker Compose Stack

A compact, production‑style demo stack that serves a “Mood of the Day” with a GIF and exposes full observability. It exists to show how a small web service behaves under caching, reverse proxying, and metrics collection — and where Docker Compose scaling starts to show its limits.

## Project overview
The Flask app generates a daily mood and GIF, caches it in Redis with a TTL, and serves it through Nginx. Prometheus scrapes metrics from the app and exporters, and Grafana visualizes them. The goal is to make the system’s behavior visible end‑to‑end while remaining simple enough to run locally.

## Architecture overview
Request flow:
```
Client → Nginx → App → Redis
                ↘ /metrics → Prometheus → Grafana
```
- **Client** hits Nginx (reverse proxy).
- **Nginx** load‑balances to the app service.
- **App** uses Redis for daily mood caching.
- **Prometheus** scrapes the app and exporters.
- **Grafana** visualizes the Prometheus data.

## Tech stack (and why it’s here)
- **Flask (Python)**: simple HTTP service with deterministic daily behavior and metrics.
- **Redis**: fast, TTL‑based cache to avoid regenerating the daily mood.
- **Nginx**: reverse proxy and load balancer; realistic front door.
- **Prometheus**: pull‑based metrics collection.
- **Grafana**: dashboards for app, Nginx, and Redis metrics.
- **Docker Compose**: local orchestration and scaling.

## Docker Compose topology
The stack uses two networks:
- **frontend**: public entry point (Nginx).
- **backend**: internal service network (app, redis, exporters, prometheus, grafana).

Services communicate over service DNS (e.g., `app`, `redis`, `prometheus`). The app does **not** expose a host port when scaled to avoid binding conflicts.

## Caching behavior (Redis)
- **Key strategy**: `mood:<YYYY-MM-DD>`
- **TTL**: seconds until midnight (daily rollover).
- **Read path**: GET returns cached mood if present; otherwise generates and caches.
- **Refresh path**: POST `/refresh` invalidates the key and writes a new mood immediately.

## Observability
### Structured JSON logging
- App logs are JSON to stdout (container logs), suitable for log shippers.
- Includes request path, container hostname, and cache status.

### Prometheus metrics
- App exposes `/metrics` on port 5000.
- Nginx and Redis metrics come from exporters.
- Example metrics:
  - `http_requests_total`
  - `http_request_latency_seconds_bucket`
  - `process_cpu_seconds_total`
  - `process_resident_memory_bytes`
  - `nginx_connections_active`
  - `redis_connected_clients`

### Grafana dashboards
A ready‑to‑import dashboard is included at:
```
monitoring/grafana/mood-app-nginx-redis.json
```
It includes sections for **App**, **Nginx**, and **Redis** with request rate, latency p95, CPU/memory, connections, and Redis ops.

## Healthchecks & self‑healing
- **App readiness**: `/health` verifies Redis connectivity.
- **App liveness**: process uptime and error rates via metrics.
- **Redis restart behavior**: data is cached; a restart simply rebuilds the key on next request.
- **Nginx traffic isolation**: only Nginx is exposed on the frontend network; app stays internal.

## Scaling strategy
- Horizontal scaling via Compose: `docker compose up --scale app=3`.
- Nginx uses service DNS (`app`) for upstream resolution.
- **No sticky sessions**: Docker DNS round‑robin makes cookie‑based affinity unreliable in Compose.

## How to run
### Build
```
docker compose build
```

### Start
```
docker compose up -d
```

### Scale the app
```
docker compose up -d --scale app=3
```

## How to access
- **Application (via Nginx)**: `http://localhost:8080`
- **Prometheus UI**: `http://localhost:9090`
- **Grafana UI**: `http://localhost:3000` (default `admin/admin`)

## Limitations & trade‑offs
- **Docker Compose only**: no service discovery beyond DNS round‑robin.
- **No sticky sessions**: Nginx OSS cannot pin to replicas behind Compose DNS.
- **No centralized log aggregation**: logs are stdout only.
- **No Kubernetes**: intentionally kept local and simple.

## Possible enhancements
- **Rate limiting** at Nginx (burst control).
- **Alerting** via Prometheus + Grafana alert rules.
- **Chaos testing** (fault injection on Redis/app).
- **CI/CD** pipeline with linting, unit tests, and container scans.
- **Kubernetes migration** with ingress and service discovery.

## Notes
This repo focuses on operational clarity: it’s small enough to run locally, yet structured like a real service stack with observability and scaling constraints made explicit.
