# 📉 Limitation: 

## Sticky Sessions with Nginx in Docker Compose
**Why cookie-based session affinity does not work when scaling**

This project attempts to implement **cookie-based sticky sessions with TTL** using Nginx. However, when the application service is scaled using Docker Compose (--scale app=N), session affinity does not work reliably.

**Root cause**

Docker Compose scales services using DNS round-robin. From Nginx’s perspective, the upstream definition:
```bash
upstream mood_app {
    server app:5000;
}
```

represents a **single backend endpoint**, even though multiple containers exist behind it. Docker’s internal DNS resolves app to different container IPs per request, which means:

* Nginx cannot see individual application containers
* Cookie-based hashing has no stable backend to bind to
* Session affinity (including TTL-based persistence) becomes ineffective

This is a known limitation of Nginx OSS combined with Docker Compose service scaling, not an application-level issue.

---

**Why defining multiple upstream servers works (but doesn’t scale)**
Session affinity does work when containers are defined explicitly:
```bash
upstream mood_app {
    hash $cookie_session_id consistent;
    server app1:5000;
    server app2:5000;
    server app3:5000;
}
```

In this setup:
* Nginx can see each backend individually
* Cookie hashing works correctly
* Sticky sessions behave as expected

However, this approach introduces a major limitation:
* Backend containers are statically defined
* Scaling requires manual changes to:
    * docker-compose.yml
    * Nginx configuration
* Dynamic scaling (auto-scaling or --scale) is not possible
This defeats the purpose of container-based elasticity.

---

Can this be solved using only Nginx?

With Nginx OSS, the options are limited:

Option	Result
Docker Compose scaling	❌ Sticky sessions break
Static upstream servers	✅ Works, but not scalable
Dynamic backend discovery	❌ Not supported
Cookie TTL stickiness	❌ Unreliable with DNS

Nginx OSS does not support dynamic service discovery or Docker API integration.

Practical conclusion

This repository intentionally demonstrates:

Where Nginx works well

Where Docker Compose introduces limitations

Why session affinity requires Docker-aware proxies or orchestration

In real-world setups, this problem is solved by:

Docker-aware reverse proxies (e.g., Traefik)

Kubernetes Ingress controllers

Service meshes

These approaches allow:

Dynamic backend discovery

Reliable sticky sessions

TTL-based connection persistence

True horizontal scaling

Why this limitation is documented (and not worked around)

Rather than forcing a static or brittle configuration, this project documents the limitation clearly to reflect real engineering constraints encountered while scaling containerized applications.

Addressing these limitations properly requires changes at the orchestration or proxy layer, which is explored further in follow-up work.

💬 One-line takeaway (interview-ready)

“Sticky sessions with Nginx break in Docker Compose scaling because Nginx cannot see individual replicas behind DNS round-robin, making cookie-based routing unreliable.”

If you want next, I can:

Write a Traefik comparison section

Add a Kubernetes Ingress equivalent

Create a diagram showing why Nginx fails here

Tighten this section further for interview clarity

You’re thinking at system-design level now 🚀