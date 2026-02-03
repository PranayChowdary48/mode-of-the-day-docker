# Mood of the Day -- Docker Compose Stack

A compact, production-style demo stack that serves a "Mood of the Day" with a GIF and exposes full observability. It exists to show how a small web service behaves under caching, reverse proxying, and metrics collection -- and where Docker Compose scaling starts to show its limits.

---

## Table of contents
- [Project overview](#project-overview)
- [Architecture overview](#architecture-overview)
- [Key capabilities](#key-capabilities)
- [Tech stack](#tech-stack)
- [Docker Compose and networking](#docker-compose-and-networking)
- [Caching strategy (Redis)](#caching-strategy-redis)
- [Observability](#observability)
  - [Structured JSON logging](#structured-json-logging)
  - [Prometheus metrics](#prometheus-metrics)
  - [Grafana dashboard](#grafana-dashboard)
- [Healthchecks and self-healing](#healthchecks-and-self-healing)
- [Scaling strategy](#scaling-strategy)
- [How to run](#how-to-run)
- [How to access](#how-to-access)
- [Limitations and trade-offs](#limitations-and-trade-offs)
- [Possible enhancements](#possible-enhancements)
- [Operational notes](#operational-notes)
- [One-line takeaway](#one-line-takeaway)

---

## Project overview
This repository is the Docker entry in a DevOps learning series (Docker -> Kubernetes -> AWS -> Automation). The main goal is to show what Docker Compose can do well for multi-service development: networking, service discovery, scaling, and observable runtime behavior.

The app generates a daily mood and GIF, caches it in Redis with a TTL, and serves it through Nginx. Prometheus scrapes metrics from the app and exporters, and Grafana visualizes them. The system is intentionally scoped to highlight Docker's capabilities and limits before moving on to the next repos in the series.

---

## Architecture overview
Request flow:
```
Client (Browser)
  ↓
Nginx (Reverse Proxy / Load Balancer)
  ↓
Python App (Flask, horizontally scaled)
  ↓
Redis (Daily cache with TTL)
```

Key design points:
- Nginx is the only public entry point.
- App containers are private and horizontally scalable.
- Redis is used for daily mood caching.
- Prometheus and Grafana provide observability.

---

## Key capabilities
- Containerized multi-service stack with repeatable local environments.
- Docker networking with isolated frontend/backend networks.
- Service discovery via Compose DNS (service-name routing).
- Horizontal scaling of the app using `docker compose up --scale`.
- Daily mood generation with TTL caching and explicit refresh.
- Structured JSON logging to stdout for log aggregation compatibility.
- Request/latency metrics exposed by the app at `/metrics`.
- Nginx and Redis metrics collected via exporters.
- Prebuilt Grafana dashboard with App/Nginx/Redis sections.

---

## Tech stack
| Component | Purpose |
| --- | --- |
| Python | Serves the application and APIs |
| Redis | Caches "mood of the day" with TTL |
| Nginx | Reverse proxy, load balancing, traffic control |
| Docker Compose | Multi-container orchestration |
| Prometheus | Metrics scraping and storage |
| Grafana | Metrics visualization and dashboards |

---

## Docker Compose and networking
Two networks are used:
- frontend:
  - exposed to the host
  - only Nginx is attached
- backend:
  - internal service network
  - app, redis, exporters, prometheus, grafana

This enforces:
- Network isolation
- No accidental direct access to app or Redis
- Clear ingress and egress boundaries

---

## Caching strategy (Redis)
### Redis key strategy
- Key format: `mood:<YYYY-MM-DD>`
- TTL: seconds until midnight (daily rollover)
- TTL is set to expire at midnight
- Cache can be manually invalidated via the UI refresh button

### Why Redis?
- Fast, simple, ephemeral
- Ideal for time-based cache with TTL
- No persistence required for this use case

---

## Observability
### Structured JSON logging
- App logs: JSON to stdout with request path, hostname, cache status, and mood.
- Nginx logs: JSON access logs to stdout and error logs to stderr.
- Suitable for shipping into ELK/Loki/Datadog later.

Example app log event:
```json
{
  "asctime":"2026-02-03 10:15:42,811",
  "levelname":"INFO",
  "message":"mood_generated",
  "container":"app-1",
  "request_path":"/",
  "cache_status":"MISS",
  "mood":"Happy"
}
```

Example Nginx access log:
```json
{
  "time":"2026-02-03T10:15:42+00:00",
  "remote_addr":"172.20.0.1",
  "request":"GET / HTTP/1.1",
  "status":200,
  "body_bytes_sent":2156,
  "request_time":0.012,
  "upstream_addr":"172.20.0.5:5000",
  "upstream_response_time":"0.011",
  "http_user_agent":"Mozilla/5.0"
}
```

### Prometheus metrics
The app exposes `/metrics` and exports:
- `http_requests_total{method,path,status}`
- `http_request_latency_seconds_bucket`
- `process_cpu_seconds_total`
- `process_resident_memory_bytes`
- `python_gc_objects_collected_total`

Nginx exporter:
- `nginx_connections_active`
- `nginx_http_requests_total`

Redis exporter:
- `redis_connected_clients`
- `redis_memory_used_bytes`
- `redis_commands_processed_total`

### Grafana dashboard
Dashboard JSON:
```
monitoring/grafana/mood-app-nginx-redis.json
```
Includes sections for:
- App: up, RPS, p95 latency, 5xx rate, CPU, memory, GC rate
- Nginx: active/reading/writing/waiting connections, RPS
- Redis: clients, memory usage, ops/sec

---

## Healthchecks and self-healing
- App readiness: `/health` checks Redis connectivity (ready vs not_ready).
- App liveness: process uptime and error rate through metrics.
- Redis restart behavior: cache is ephemeral; data is restored on next request.
- Nginx isolation: only Nginx is exposed on the frontend network.
- Restart policy: containers restart unless stopped (`restart: unless-stopped`).

---

## Scaling strategy
- Horizontal scaling via Compose: `docker compose up --scale app=3`.
- Nginx upstream resolves `app` via Docker DNS round-robin.
- No sticky sessions: cookie-based affinity cannot target specific replicas.

---

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

---

## How to access
- Application (via Nginx): `http://localhost:8080`
- Prometheus UI: `http://localhost:9090`
- Grafana UI: `http://localhost:3000` (default `admin/admin`)

---

## Limitations and trade-offs
### Docker / Compose constraints
- DNS round-robin only: no service discovery metadata, no per-replica visibility.
- No sticky sessions: Nginx OSS cannot pin to replicas behind DNS.
- Limited routing control: cannot dynamically reconfigure Nginx upstreams.
- Single host assumptions: no multi-node orchestration.
- No native autoscaling: scaling is manual (`--scale`) without metrics-driven automation.
- No built-in secrets management: relies on env vars or external tooling.
- No native traffic policies: retries, circuit breaking, and canary need extra tooling.

### Observability constraints
- No centralized log aggregation: logs are stdout only.
- Limited per-route latency: histogram is not broken down by path.
- No alert rules shipped by default.
- No SLOs / SLIs defined.

### Security / production hardening
- Default Grafana creds (admin/admin).
- No TLS termination on Nginx.
- No auth on app.
- No rate limiting or WAF.

### Reliability constraints
- Redis is single-instance: no replication or persistence.
- No blue/green deploy strategy.
- No automatic rollback or CI/CD.

---

## Possible enhancements
### Reliability and scaling
- Add Redis persistence (AOF/RDB) or Redis Sentinel.
- Use Traefik or Envoy for real service discovery.
- Migrate to Kubernetes for ingress and autoscaling.
- Add Compose profiles for dev/test/observability splits.
- Add blue/green or canary deployment patterns in the Kubernetes follow-up repo.

### Observability
- Add Prometheus alert rules (latency, error rate, Redis memory).
- Add Grafana provisioning to auto-load dashboards.
- Ship logs to Loki/ELK with labels and correlation IDs.
- Add trace IDs and OpenTelemetry instrumentation.
- Add RED metrics dashboard (Rate, Errors, Duration) per endpoint.

### Security
- Add TLS via certbot or nginx-ssl.
- Add authentication for `/refresh` and `/metrics`.
- Add rate limiting or abuse protection.
- Add secret rotation via Docker secrets or external vault.

### App features
- Per-route latency metrics.
- Cache hit ratio metric.
- User-specific mood personalization.

### Operational maturity
- CI/CD pipeline with tests, linting, and container scanning.
- Chaos testing for Redis outages.
- Load testing with k6 or Locust.
- Automated image publishing with versioned tags and SBOMs.

---

## Operational notes
- Rebuild after app changes:
```
docker compose up -d --build
```
- Scale without host port collisions: keep `app` internal.
- Dashboard import: Grafana -> + -> Import -> JSON file.

---

## One-line takeaway
This repo is the Docker chapter of a DevOps series: it intentionally keeps Docker-only limitations visible before the **Kubernetes** and **AWS** follow-ups (https://github.com/example/mood-of-the-day-k8s).
