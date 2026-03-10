# Plan: GitHub Copilot Agentic Workshop — v3

**TL;DR**: 75-min core workshop + take-home exercises. Attendees fork a **prepared repo with checkpoint branches** — if they fall behind, they merge a checkpoint in 3 clicks and keep going. The centerpiece is a fully autonomous agentic SDLC pipeline: daily scans → auto-created issues → Copilot fixes → CI validates → Code Review → human approves.

---

## Branch Strategy

```
main                          ← Clean repo, zero Copilot/DevSecOps config (starting point)
│
├── checkpoint/module-2       ← copilot-instructions.md + dependabot.yml + codeql.yml
│
├── checkpoint/module-4       ← module-2 content + security-audit-autofix.yml
│
├── checkpoint/complete       ← everything (all workflows, bonus content)
│
└── demo/devsecops-results    ← Facilitator's branch with pre-baked Dependabot/CodeQL results
```

**How it works**:

- Attendees fork → get `main` + all checkpoint branches
- They work on `main`, creating files via github.com UI
- **If they fall behind**: create a PR from `checkpoint/module-X` → `main` → merge → caught up in 3 clicks
- **Copilot Coding Agent** creates its own branches (`copilot/fix-xxx-123`) targeting `main` — no conflicts with checkpoints
- **Facilitator demos** Module 3 from a separate pre-baked fork (Dependabot/CodeQL need 30+ min warmup)

**Facilitator prepares** the source repo 1-2 days before: create the checkpoint branches with the correct cumulative file content, plus a separate fork where Dependabot/CodeQL have already run.

---

## Workshop Modules (~75 min core + take-home)

### Module 0: Welcome + Orientation (8 min) — `main`

- Architecture overview (8 polyglot microservices, event-driven)
- Key point: repo has **zero DevSecOps** — no Dependabot, no CodeQL, no scanning, no Copilot config
- Explain branch strategy: work on `main`, checkpoint branches are your safety net
- Confirm forks ready, Actions enabled, Coding Agent enabled, `PAT_TOKEN` secret set

### Module 1: Copilot Chat — Security Assessment (10 min) — `main`

_Topic: github.com agentic features_

Attendees use Copilot Chat on github.com to audit the repo:

- "What DevSecOps tooling is configured?" → answer: none
- "Find hardcoded credentials, missing validation, loose dep versions"
- "Which services have no unit tests?"

**Takeaway**: Full-repo security assessment in seconds via Chat.

### Module 2: Foundation — Instructions + DevSecOps Config (12 min) — `main` / checkpoint: `checkpoint/module-2`

_Topic: custom/agentic SDLC_

Create 3 files via github.com UI:

**1. `.github/copilot-instructions.md`** — coding standards, security requirements

```markdown
# Copilot Instructions for aks-store-demo

## Project Context

Polyglot microservices demo: JavaScript (Fastify), Go (Gin), Rust (Actix), Python (FastAPI), Vue.js 3.

## Coding Standards

- Go: standard layout, table-driven tests, golint compliant
- Node.js: Fastify patterns, TAP test framework, schema-based validation
- Python: pytest, type hints, input validation on all endpoints
- Rust: idiomatic, doc comments, cargo clippy clean

## Security Requirements

- No hardcoded secrets — use environment variables
- Validate all user input at API boundaries
- Pin dependency versions (no caret ranges for production)
- All PRs must include tests for new/changed code
```

**2. `.github/dependabot.yml`** — daily scanning for npm/pip/gomod/cargo/actions — **all with `assignees: ["copilot"]`**

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
  - package-ecosystem: "npm"
    directory: "/src/store-admin"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
  - package-ecosystem: "pip"
    directory: "/src/ai-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
  - package-ecosystem: "gomod"
    directory: "/src/makeline-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
  - package-ecosystem: "cargo"
    directory: "/src/product-service"
    schedule:
      interval: "daily"
    assignees:
      - "copilot"
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: "weekly"
    assignees:
      - "copilot"
```

**3. `.github/workflows/codeql.yml`** — CodeQL for JS, Python, Go

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
      matrix:
        language: [javascript-typescript, python, go]
    steps:
      - uses: actions/checkout@v4
      - uses: github/codeql-action/init@v3
        with:
          languages: ${{ matrix.language }}
      - uses: github/codeql-action/autobuild@v3
      - uses: github/codeql-action/analyze@v3
```

Fall behind? → Merge `checkpoint/module-2` into `main`.

**Takeaway**: `assignees: copilot` in Dependabot means dependency PRs go straight to the Coding Agent. Three files set up the full DevSecOps foundation.

### Module 3: DevSecOps Showcase (10 min) — facilitator's pre-baked fork

_Topic: agentic SDLC, DevSecOps_

Facilitator demos live from a fork where Dependabot/CodeQL have already run:

1. Dependabot Alerts → vulnerabilities across all ecosystems
2. Dependabot PRs → auto-generated, some assigned to Copilot
3. CodeQL Security tab → code scanning alerts
4. **Copilot Autofix** → click alert → AI proposes inline fix → one-click apply
5. Secret Scanning → flagged patterns

**Key narrative**: runs daily, autonomously, zero human effort to identify and fix.

### Module 4: Agentic Workflows — Automated Issue Pipeline (20 min) — `main` / checkpoint: `checkpoint/module-4`

_Topic: agentic workflows, automated actions, auto-assign to Copilot_ — **core module**

Create **`.github/workflows/security-audit-autofix.yml`** with 3 parallel jobs:

| Job                   | What it does                   | Output                                        |
| --------------------- | ------------------------------ | --------------------------------------------- |
| `audit-node`          | `npm audit` on order-service   | Creates security issue → assigns to `copilot` |
| `audit-python`        | `pip-audit` on ai-service      | Creates security issue → assigns to `copilot` |
| `test-coverage-check` | Finds services with zero tests | Creates quality issue → assigns to `copilot`  |

```yaml
name: "Security Audit → Auto-Create Issues → Assign to Copilot"

on:
  schedule:
    - cron: "0 8 * * 1-5" # Weekdays at 8am UTC
  workflow_dispatch: # Manual trigger for demo

permissions:
  contents: read
  issues: write

jobs:
  audit-node:
    name: Audit Node.js Services
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Audit order-service
        id: audit
        run: |
          cd src/order-service
          npm install --package-lock-only 2>/dev/null
          set +e
          AUDIT_OUTPUT=$(npm audit --json 2>/dev/null)
          set -e
          HIGH=$(echo "$AUDIT_OUTPUT" | jq '.metadata.vulnerabilities.high // 0')
          CRITICAL=$(echo "$AUDIT_OUTPUT" | jq '.metadata.vulnerabilities.critical // 0')
          TOTAL=$((HIGH + CRITICAL))
          echo "total=$TOTAL" >> "$GITHUB_OUTPUT"
          echo "$AUDIT_OUTPUT" | jq -r '[.vulnerabilities | to_entries[] | select(.value.severity == "high" or .value.severity == "critical") | "- **\(.key)** (\(.value.severity)): \(.value.via[0].title // "unknown")"] | join("\n")' > findings.md

      - name: Create issue and assign to Copilot
        if: steps.audit.outputs.total != '0'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const findings = fs.readFileSync('findings.md', 'utf8');
            const existing = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'security,automated,order-service',
              state: 'open'
            });
            if (existing.data.length > 0) {
              console.log('Issue already exists, skipping');
              return;
            }
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '[Security] Fix npm vulnerabilities in order-service',
              body: [
                '## Automated Security Audit Finding',
                '',
                '**Service:** order-service (`src/order-service/`)',
                '**Scanner:** npm audit',
                `**Found:** ${process.env.TOTAL || 'multiple'} high/critical vulnerabilities`,
                '',
                '### Vulnerabilities',
                findings,
                '',
                '### Remediation',
                'Update affected dependencies in `src/order-service/package.json` to patched versions.',
                '- Run `npm audit fix` or manually update versions',
                '- Ensure all existing tests still pass',
                '- Pin versions to exact (remove caret ranges) where possible',
                '',
                '> This issue was auto-generated by the security audit workflow.'
              ].join('\n'),
              labels: ['security', 'automated', 'order-service'],
              assignees: ['copilot']
            });

  audit-python:
    name: Audit Python Services
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Audit ai-service
        id: audit
        run: |
          pip install pip-audit 2>/dev/null
          set +e
          AUDIT_OUTPUT=$(pip-audit -r src/ai-service/requirements.txt --format json 2>/dev/null)
          set -e
          VULN_COUNT=$(echo "$AUDIT_OUTPUT" | jq '[.dependencies[] | select(.vulns | length > 0)] | length')
          echo "count=${VULN_COUNT:-0}" >> "$GITHUB_OUTPUT"
          echo "$AUDIT_OUTPUT" | jq -r '[.dependencies[] | select(.vulns | length > 0) | "- **\(.name)** \(.version): \(.vulns[0].id) — \(.vulns[0].description // "see advisory")"] | join("\n")' > findings.md

      - name: Create issue and assign to Copilot
        if: steps.audit.outputs.count != '0'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const findings = fs.readFileSync('findings.md', 'utf8');
            const existing = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'security,automated,ai-service',
              state: 'open'
            });
            if (existing.data.length > 0) return;
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '[Security] Fix Python dependency vulnerabilities in ai-service',
              body: [
                '## Automated Security Audit Finding\n',
                '**Service:** ai-service (`src/ai-service/`)',
                '**Scanner:** pip-audit\n',
                '### Vulnerabilities',
                findings,
                '\n### Remediation',
                'Update affected packages in `src/ai-service/requirements.txt` to patched versions.',
                'Verify the FastAPI app starts and existing functionality works.\n',
                '> Auto-generated by security audit workflow.'
              ].join('\n'),
              labels: ['security', 'automated', 'ai-service'],
              assignees: ['copilot']
            });

  test-coverage-check:
    name: Check Test Coverage Gaps
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Identify untested services
        id: coverage
        run: |
          GAPS=""
          if ! find src/makeline-service -name "*_test.go" | grep -q .; then
            GAPS="${GAPS}- **makeline-service** (Go): Zero test files found\n"
          fi
          if ! find src/ai-service -name "test_*" -o -name "*_test.py" | grep -q .; then
            GAPS="${GAPS}- **ai-service** (Python): Zero test files found\n"
          fi
          if ! grep -r "#\[test\]" src/product-service/src/ 2>/dev/null | grep -q .; then
            GAPS="${GAPS}- **product-service** (Rust): No unit test modules found\n"
          fi
          if [ -n "$GAPS" ]; then
            echo "has_gaps=true" >> "$GITHUB_OUTPUT"
            printf "%b" "$GAPS" > gaps.md
          else
            echo "has_gaps=false" >> "$GITHUB_OUTPUT"
          fi

      - name: Create issue for test gaps
        if: steps.coverage.outputs.has_gaps == 'true'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const gaps = fs.readFileSync('gaps.md', 'utf8');
            const existing = await github.rest.issues.listForRepo({
              owner: context.repo.owner,
              repo: context.repo.repo,
              labels: 'testing,automated',
              state: 'open'
            });
            if (existing.data.length > 0) return;
            await github.rest.issues.create({
              owner: context.repo.owner,
              repo: context.repo.repo,
              title: '[Quality] Add unit tests for untested services',
              body: [
                '## Automated Test Coverage Finding\n',
                '### Services Missing Unit Tests',
                gaps,
                '\n### Requirements',
                '- Go services: use `testing` package with table-driven tests',
                '- Python services: use `pytest` with fixtures, mock external APIs',
                '- Rust services: use `#[cfg(test)]` module with unit tests\n',
                '> Auto-generated by test coverage check workflow.'
              ].join('\n'),
              labels: ['testing', 'automated'],
              assignees: ['copilot']
            });
```

**Live flow**: paste YAML → commit → Actions tab → "Run workflow" → watch issues appear → "Copilot is working" → PRs generated.

Discuss the agentic loop while waiting: scan → issue → agent plans → codes → CI runs → agent reads failure → fixes → repushes → PR ready.

Fall behind? → Merge `checkpoint/module-4`.

**Takeaway**: This is the agentic workflow — an automated pipeline that finds problems and delegates fixes to an AI agent on a daily schedule.

### Module 5: Coding Agent + Code Review — Full Loop (15 min) — `main` + Copilot's branches

_Topic: agentic loops, Code Review_

By now, Copilot should have PRs from auto-created issues.

**Demo**:

1. Open a PR Copilot created → show commit history (iterations: plan → code → CI fail → fix → pass)
2. Request Copilot as reviewer → show review comments
3. Reply to a review comment → Copilot responds

**Hands-on**:

1. Check PRs from Module 4's auto-created issues
2. Manually create 1 additional issue → assign to Copilot:
   - "Add input validation to order-service POST /order" (easy)
   - "Add /health and /ready endpoints to makeline-service" (medium)
   - "Remove hardcoded RabbitMQ creds from docker-compose.yml" (easy/security)
3. Add Copilot as reviewer on completed PRs
4. Reply to review comments — ask Copilot to refine
5. Verify: did the agent follow custom instructions from Module 2?

**Takeaway**: The full loop — auto-scan → issue → agent codes → CI validates → agent iterates → code review → human approves.

### Module 6: IaC Security Agent — Custom Copilot Agent for DevSecOps (10 min) — `main`

_Topic: custom agents, DevSecOps, agentic SDLC_

Create a **custom Copilot agent** that specializes in scanning Infrastructure-as-Code for security misconfigurations. This repo is perfect — it has Terraform, Bicep, Kubernetes manifests, Helm charts, and Dockerfiles.

**Demo (3 min)**: Explain custom agents — specialized versions of Copilot with domain expertise, defined as markdown files in `.github/agents/`.

**Hands-on (7 min)**: Attendees create `.github/agents/iac-security-agent.md` via github.com UI.

This agent:

- Scans Terraform (`infra/terraform/`), Bicep (`infra/bicep/`), K8s manifests (`kustomize/`, `aks-store-*.yaml`), Helm charts (`charts/`), and Dockerfiles
- Categorizes findings by: IAM, Network Security, Data Protection, Logging, Container Security
- Maps findings to CIS Azure, NIST 800-53, Azure Security Benchmark
- Produces a structured security report with remediation diffs

**After creating**: Go to any issue → create a new issue → type `@copilot Use the IaCSecurityAgent to scan this repository's infrastructure code and generate a security report` → assign to Copilot.

**Takeaway**: Custom agents let you create specialized, reusable Copilot personas for recurring tasks. The IaC security agent turns ad-hoc security reviews into a repeatable, automated process.

### Module 7: GitHub Agentic Workflows — Markdown-Defined Automation (10 min) — `main`

_Topic: agentic workflows, GitHub Agentic Workflows (gh-aw)_

**Concept**: GitHub Agentic Workflows (`gh aw`) let you write repository automation in **markdown** instead of complex YAML. An AI agent (Copilot, Claude, or Codex) executes the workflow in a sandboxed environment with guardrails.

**Demo (5 min)**: Show the concept — a `.github/workflows/security-report.md` file that defines a daily security report workflow in natural language:

```markdown
---
on:
  schedule: weekly
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
safe-outputs:
  create-issue:
    title-prefix: "[security-report] "
    labels: [security, report, automated]
    close-older-issues: true
---

## Weekly IaC Security Report

Scan all infrastructure-as-code files in this repository and generate a comprehensive security report as a GitHub issue.

## What to scan

- Terraform files in `infra/terraform/`
- Bicep files in `infra/bicep/`
- Kubernetes manifests in `kustomize/` and root `aks-store-*.yaml` files
- Helm charts in `charts/`
- Dockerfiles in each `src/*/Dockerfile`

## What to report

- Misconfigurations and insecure defaults
- Findings grouped by: Identity & Access, Network Security, Data Protection, Container Security, Logging
- Severity classification: Critical, High, Medium, Low
- Specific file paths and line numbers for each finding
- Recommended fixes with code snippets
- Compliance mapping to CIS Azure and NIST 800-53 where applicable

## Report format

Use a structured markdown report with summary table and detailed findings sections.
```

**Hands-on (5 min)**: Attendees create this workflow file via github.com UI. Then:

1. Install the `gh-aw` CLI extension (or use the web interface)
2. Compile: `gh aw compile` generates the `.lock.yml` action file
3. Trigger: Actions tab → "Run workflow" or `gh aw run security-report`

**Key narrative**: This is the next evolution — you don't write YAML pipelines anymore, you describe what you want in markdown and an AI agent executes it. Combine this with the IaC security agent for a fully autonomous security review pipeline.

**Takeaway**: GitHub Agentic Workflows are "Continuous AI" — scheduled, recurring AI automation defined in natural language with built-in guardrails.

### Recap + Wrap-Up (5 min)

```
┌─────────────────────────────────────────────────────────────────┐
│                    YOUR AGENTIC SDLC PIPELINE                   │
│                                                                 │
│  Scheduled Actions ──▶ GitHub Issue ──▶ Copilot Coding Agent    │
│  (npm audit, pip-       (auto-created,   (plans, codes,         │
│   audit, CodeQL,         auto-assigned)   iterates with CI)     │
│   Dependabot)                                     │             │
│                                                    ▼             │
│  Human Approves ◀── Copilot Code Review ◀── GitHub Actions CI   │
│  & Merges            (catches issues)       (tests, lint, scan) │
│                                                                 │
│  Custom Instructions shape ALL agent behavior at every step     │
└─────────────────────────────────────────────────────────────────┘
```

**What's now running on your fork daily**:

- Dependabot scans 6 ecosystems → creates PRs → assigns to Copilot
- CodeQL scans JS/Python/Go on every push + weekly
- Security audit workflow scans daily → creates issues → assigns to Copilot
- **Check your fork tomorrow** — you'll have new issues and PRs waiting

**Topics roundup**:

| Workshop Topic              | Where Covered                                                                  |
| --------------------------- | ------------------------------------------------------------------------------ |
| github.com agentic features | Module 1 (Chat), Module 5 (Code Review), Module 6 (Custom Agents)              |
| Agentic loops               | Module 4 (scan→issue→agent→CI→iterate), Module 5 (commit history)              |
| Agentic workflows           | Module 4 (automated pipeline), Module 2 (Dependabot+Copilot), Module 7 (gh-aw) |
| Custom/agentic SDLC         | Module 2 (instructions), Module 3 (DevSecOps), Module 6 (IaC agent), Recap     |
| DevSecOps showcase          | Module 3 (Autofix), Module 6 (IaC security agent), Module 7 (security report)  |

---

## Take-Home Exercises (async, post-workshop)

1. **Check Dependabot/CodeQL results** — next day, review alerts and Copilot Autofix on your fork
2. **Container scan workflow** — create a Trivy-based docker-scan.yml (Trivy scans Docker images → auto-creates issues → assigns to Copilot). Available in `checkpoint/complete`.
3. **More Copilot issues** — create and assign to Copilot:
   - Add pytest tests for ai-service
   - Add Go unit tests for makeline-service
   - Create API documentation for all services
   - Add OpenAPI spec for order-service
   - Create .github/CODEOWNERS
4. **Branch protection rules** — require Copilot Code Review + CI pass before merge
5. **Extend the pipeline** — add govulncheck for Go, cargo-audit for Rust, SBOM generation

---

## Pre-Workshop Checklist (Facilitator)

- [ ] Prepare source repo with checkpoint branches (`checkpoint/module-2`, `checkpoint/module-4`, `checkpoint/complete`)
- [ ] Create a separate pre-baked fork with Dependabot/CodeQL results (30+ min lead time)
- [ ] Prepare handout with all YAML snippets and issue bodies (copy-paste ready)
- [ ] Verify Copilot Business/Enterprise license with Coding Agent enabled at org level
- [ ] Prepare slides: agentic AI concepts, Copilot product map, aks-store-demo architecture diagram
- [ ] Dry-run full pipeline end-to-end
- [ ] Communicate to attendees: fork the repo + enable GitHub Actions before the workshop

## Pre-Workshop Checklist (Attendees)

- [ ] Fork the repo to your own GitHub account
- [ ] Enable GitHub Actions on the fork (Settings → Actions → General → Allow all actions)
- [ ] Verify Copilot is available on github.com (open Copilot Chat on the repo page)
- [ ] Create a `PAT_TOKEN` repo secret (Fine-grained PAT with Read & Write for: Actions, Contents, Issues, Pull requests) — required for auto-assigning Copilot to issues in Module 4

## Risks & Mitigations

| Risk                                 | Impact                                   | Mitigation                                                                |
| ------------------------------------ | ---------------------------------------- | ------------------------------------------------------------------------- |
| Coding Agent not enabled             | Blocker — can't assign issues to Copilot | Verify per-attendee beforehand; facilitator live-demos as fallback        |
| Agent latency (3-8 min per PR)       | Waiting time in Module 4                 | Trigger early, discuss concepts while waiting                             |
| Actions minutes exhausted            | Workflows fail                           | Use org with paid plan; warn free-tier users (~50 min/attendee)           |
| Dependabot/CodeQL warmup (15-30 min) | No live results in Module 3              | Module 3 uses facilitator's pre-baked fork; attendees see theirs next day |
| Attendee falls behind                | Can't proceed to next module             | Merge checkpoint branch (3 clicks on github.com)                          |
