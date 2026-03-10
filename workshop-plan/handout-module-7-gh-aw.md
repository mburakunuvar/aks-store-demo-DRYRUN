# Handout: Module 7 — GitHub Agentic Workflows (gh-aw)

> **What you'll do**: Create a markdown-defined agentic workflow that generates a weekly IaC security report — no YAML required. The AI agent reads your repo, analyzes infrastructure code, and creates a security report as a GitHub issue.
>
> **Pre-requisite**: `gh` CLI with the `gh-aw` extension installed, OR use the github.com Copilot Chat to create the workflow.

---

## Concept

GitHub Agentic Workflows (`gh aw`) let you define repository automation in **markdown** instead of YAML. An AI agent (Copilot, Claude, or Codex) executes the workflow in a sandboxed GitHub Actions environment with built-in guardrails.

Key differences from regular GitHub Actions:

- **Markdown, not YAML** — define what you want in natural language
- **AI-powered execution** — a coding agent interprets and acts on your instructions
- **Safe outputs** — write operations (create issue, comment on PR) are pre-approved and sandboxed
- **Guardrails** — read-only by default, network isolation, tool allowlisting

---

## Option A: Create via github.com Copilot Chat (no CLI needed)

On your fork, open Copilot Chat and enter:

```
Create a workflow for GitHub Agentic Workflows using https://raw.githubusercontent.com/github/gh-aw/main/create.md

The purpose of the workflow is a weekly IaC security report that scans Terraform (infra/terraform/), Bicep (infra/bicep/), Kubernetes manifests (kustomize/, aks-store-*.yaml), Helm charts (charts/), and Dockerfiles (src/*/Dockerfile) for security misconfigurations. Generate findings grouped by IAM, Network Security, Data Protection, Container Security, and Logging. Deliver the report as a GitHub issue.
```

Copilot will create the workflow file and its lock file for you.

---

## Option B: Create manually

### File: `.github/workflows/security-report.md`

**Path**: `.github/workflows/security-report.md`

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

Use a structured markdown report with:

- Summary table (category × severity counts)
- Detailed findings with file, line, issue, impact, and remediation
- A "Quick Wins" section listing the top 5 easiest fixes with highest impact
```

### Compile and push

If using the CLI:

```bash
# Install the gh-aw extension (once)
gh extension install github/gh-aw

# Compile the markdown into a GitHub Actions workflow
gh aw compile

# This generates .github/workflows/security-report.lock.yml
# Commit both files
git add .github/workflows/security-report.md .github/workflows/security-report.lock.yml
git commit -m "add weekly IaC security report agentic workflow"
git push
```

### Set up the engine secret

Go to **Settings → Secrets → Actions** and add the secret for your chosen AI engine:

| Engine                    | Secret name            | Where to get it                   |
| ------------------------- | ---------------------- | --------------------------------- |
| **Copilot** (recommended) | `COPILOT_GITHUB_TOKEN` | Same PAT you created for Module 4 |
| Claude                    | `ANTHROPIC_API_KEY`    | https://console.anthropic.com/    |
| Codex                     | `OPENAI_API_KEY`       | https://platform.openai.com/      |

### Trigger the workflow

Go to **Actions** tab → **"Weekly IaC Security Report"** → **"Run workflow"**

Within 2-3 minutes, a new issue will be created with a comprehensive security report.

---

## What This Demonstrates

- **Next-gen automation**: Define workflows in natural language, not YAML
- **Continuous AI**: Scheduled, recurring AI tasks that run automatically
- **Guardrails**: Safe outputs ensure the AI can only perform pre-approved operations
- **Composability**: Agentic workflows can reference your custom agents (Module 6) for specialized tasks
- **DevSecOps evolution**: Security reviews that happen automatically, every week, without human effort

---

## Resources

- Docs: https://github.github.com/gh-aw/
- Quick Start: https://github.github.com/gh-aw/setup/quick-start/
- Creating Workflows: https://github.github.com/gh-aw/setup/creating-workflows/
- Example Gallery: https://github.github.com/gh-aw/#gallery
