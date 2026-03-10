# Handout: Module 2 — Foundation Setup

> **What you'll do**: Create 3 files on your fork via github.com UI to set up Copilot custom instructions, Dependabot with auto-assign to Copilot, and CodeQL code scanning.
>
> **How**: On your fork → click "Add file" → "Create new file" → paste content → commit to `main`.
>
> **If you fall behind**: Go to your fork → create a PR from `checkpoint/module-2` → `main` → merge it.

---

## File 1: `.github/copilot-instructions.md`

**Path**: `.github/copilot-instructions.md`

```markdown
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
```

---

## File 2: `.github/dependabot.yml`

**Path**: `.github/dependabot.yml`

> Key detail: every entry has `assignees: ["copilot"]` — this means Dependabot PRs are automatically assigned to the Copilot Coding Agent.

```yaml
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/src/order-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "security"
      - "automated"

  - package-ecosystem: "npm"
    directory: "/src/store-front"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "automated"

  - package-ecosystem: "npm"
    directory: "/src/store-admin"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "automated"

  - package-ecosystem: "pip"
    directory: "/src/ai-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "automated"

  - package-ecosystem: "gomod"
    directory: "/src/makeline-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "automated"

  - package-ecosystem: "cargo"
    directory: "/src/product-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "automated"

  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    assignees:
      - "copilot"
    labels:
      - "dependencies"
      - "ci"
      - "automated"
```

---

## File 3: `.github/workflows/codeql.yml`

**Path**: `.github/workflows/codeql.yml`

```yaml
name: "CodeQL Analysis"

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"

jobs:
  analyze:
    name: Analyze (${{ matrix.language }})
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      contents: read
      actions: read
    strategy:
      fail-fast: false
      matrix:
        language: [javascript-typescript, python, go]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Initialize CodeQL
        uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}

      - name: Autobuild
        uses: github/codeql-action/autobuild@v3

      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v3
```

---

## Verification

After committing all 3 files, confirm they appear in your repo:

- `https://github.com/<you>/aks-store-demo/blob/main/.github/copilot-instructions.md`
- `https://github.com/<you>/aks-store-demo/blob/main/.github/dependabot.yml`
- `https://github.com/<you>/aks-store-demo/blob/main/.github/workflows/codeql.yml`
