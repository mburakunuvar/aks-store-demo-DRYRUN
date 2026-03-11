# Handout: Module 5 — Manual Issues for Copilot Coding Agent

> **What you'll do**: Create 1–2 issues on your fork and assign them to Copilot. The Coding Agent will pick them up, create a branch, implement the changes, and open a PR.
>
> **How**: On your fork → **Issues** tab → **"New issue"** → paste title + body → set **Assignees** to `copilot` → **"Submit new issue"**.

---

## Pick 1–2 issues from this menu:

### Issue A: Add Input Validation (Node.js — Easy)

**Title:**

```
Add input validation to order-service POST /order endpoint
```

**Body:**

```markdown
## Description

The order-service (`src/order-service/`) accepts orders via POST /order without validating the request body. Add Fastify schema-based request validation.

## Requirements

- Add a JSON schema to the POST /order route for request body validation
- Required fields: `storeId` (string), `customerOrderId` (string), `items` (array)
- `items` array must not be empty
- Each item needs `productId` (integer) and `quantity` (positive integer)
- Return 400 with a descriptive error for invalid payloads
- Add TAP tests for both valid and invalid payloads in `test/`

## Files to modify

- `src/order-service/routes/` — add schema to the order route
- `src/order-service/test/` — add validation tests
```

**Labels:** `enhancement`
**Assignees:** `copilot`

---

### Issue B: Add Health Endpoints (Go — Medium)

**Title:**

```
Add /health and /ready endpoints to makeline-service
```

**Body:**

```markdown
## Description

The makeline-service (`src/makeline-service/`) needs Kubernetes health check endpoints for liveness and readiness probes.

## Requirements

- `GET /health` — liveness probe: returns HTTP 200 with `{"status": "ok"}` if the process is running
- `GET /ready` — readiness probe: returns HTTP 200 only if the MongoDB/CosmosDB connection is established; returns 503 otherwise
- Add both endpoints to `main.go` using the Gin router
- Add table-driven unit tests in a new `health_test.go` file
- Update `src/makeline-service/README.md` with the new endpoints

## Files to modify

- `src/makeline-service/main.go`
- `src/makeline-service/health_test.go` (new file)
- `src/makeline-service/README.md`
```

**Labels:** `enhancement`
**Assignees:** `copilot`

---

### Issue C: Remove Hardcoded Credentials (Security — Easy)

**Title:**

```
Remove hardcoded RabbitMQ credentials from docker-compose files
```

**Body:**

```markdown
## Description

The docker-compose.yml and docker-compose-quickstart.yml contain hardcoded RabbitMQ credentials (`username`, `password`). These should be externalized.

## Requirements

- Create a `.env.example` file with placeholder values for RabbitMQ credentials
- Update `docker-compose.yml` to reference environment variables instead of hardcoded values
- Update `docker-compose-quickstart.yml` similarly
- Add `.env` to `.gitignore` to prevent committing real credentials
- Document the change in the root `README.md` (add a note about copying `.env.example` to `.env`)

## Files to modify

- `docker-compose.yml`
- `docker-compose-quickstart.yml`
- `.env.example` (new file)
- `.gitignore`
- `README.md`
```

**Labels:** `security`
**Assignees:** `copilot`

---

### Issue D: Create API Documentation (Docs — Easy)

**Title:**

```
Create API documentation for order-service
```

**Body:**

```markdown
## Description

The order-service (`src/order-service/`) lacks API documentation. Create a markdown doc with all endpoints.

## Requirements

- Create `docs/api/order-service.md`
- Document all REST endpoints: method, path, request/response schemas
- Include environment variables and configuration options
- Add example curl commands for each endpoint
- Document error responses and status codes

Review the route handlers in `src/order-service/routes/` and `src/order-service/app.js` for accuracy.

## Files to create

- `docs/api/order-service.md`
```

**Labels:** `documentation`
**Assignees:** `copilot`

---

## After Creating Issues

1. Watch the **Issues** tab — within ~1 minute you should see "Copilot is working" on assigned issues
2. Within ~5 minutes, check the **Pull Requests** tab for Copilot's PRs
3. Open a PR → check the commit history to see the agentic loop (plan → code → CI → fix → iterate)
4. **Add Copilot as a reviewer** on the PR:
   - Click "Reviewers" → type `copilot` → select it
   - Read through Copilot's review comments
   - Reply to a comment — ask Copilot to refine something
5. Check: did the agent follow the custom instructions you created in Module 2?
