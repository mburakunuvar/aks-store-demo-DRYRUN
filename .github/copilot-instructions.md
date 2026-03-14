# Copilot Instructions for aks-store-demo

## Project Context

Polyglot microservices demo for Azure Kubernetes Service with 8 services:

- **order-service** — JavaScript / Node.js (Fastify)
- **makeline-service** — Go (Gin)
- **product-service** — Rust (Actix-web)
- **ai-service** — Python (FastAPI)
- **store-front** — Vue.js 3 (TypeScript / Vite)
- **store-admin** — Vue.js 3 (TypeScript / Vite)
- **virtual-customer** — Rust (load simulator)
- **virtual-worker** — Rust (load simulator)

Data flow: customer → store-front → order-service → RabbitMQ → makeline-service → MongoDB/CosmosDB

## Coding Standards

- **Go**: standard project layout, table-driven tests using `testing` package, `golint` compliant
- **Node.js**: Fastify patterns, TAP test framework, Fastify schema-based request validation
- **Python**: pytest with fixtures, type hints required, input validation on all endpoints
- **Rust**: idiomatic Rust, doc comments on public items, `cargo clippy` clean, `#[cfg(test)]` modules
- **Vue.js**: Composition API, TypeScript strict mode, Vitest for unit tests

## Security Requirements

- No hardcoded secrets — use environment variables or mounted secrets
- Validate all user input at API boundaries
- Pin dependency versions explicitly (no caret ranges for production dependencies)
- All PRs must include tests for new or changed code
- Docker images should use specific base image tags, not `latest`

## PR Standards

- PRs must include a clear description of what changed and why
- Link related issues using `Fixes #N` or `Closes #N`
- Include evidence that tests pass (CI green or manual test output)
