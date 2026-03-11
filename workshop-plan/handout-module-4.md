# Handout: Module 4 — Agentic Workflow (Security Audit Pipeline)

> **What you'll do**: Create a GitHub Actions workflow that automatically scans for vulnerabilities, creates GitHub Issues, and assigns them to Copilot Coding Agent — fully automated.
>
> **Pre-requisite**: You need a `PAT_TOKEN` secret in your repo (see below).
>
> **How**: On your fork → "Add file" → "Create new file" → paste content → commit to `main`.
>
> **After committing**: Go to **Actions** tab → select the workflow → click **"Run workflow"** → watch it create issues and assign to Copilot.
>
> **If you fall behind**: Go to your fork → create a PR from `checkpoint/module-4` → `main` → merge it.

---

## Pre-requisite: Create PAT_TOKEN secret

The workflow needs a Personal Access Token (PAT) to assign Copilot to issues. The default `GITHUB_TOKEN` doesn't carry your Copilot entitlement.

1. Go to **<https://github.com/settings/tokens>s>** → **Fine-grained tokens** → **Generate new token**
2. **Token name**: `workshop-copilot-assign`
3. **Repository access**: select your fork of `aks-store-demo`
4. **Permissions** (all Read & Write):
   - **Actions** → Read and Write
   - **Contents** → Read and Write
   - **Issues** → Read and Write
   - **Pull requests** → Read and Write
5. Click **Generate token** → copy the token
6. Go to your fork → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**
7. **Name**: `PAT_TOKEN`
8. **Value**: paste the token
9. Click **Add secret**

---

## File: `.github/workflows/security-audit-autofix.yml`

**Path**: `.github/workflows/security-audit-autofix.yml`

This workflow has 3 parallel jobs. Each scans for issues, creates a GitHub Issue, then assigns Copilot via the REST API using your PAT:

| Job                   | Scanner     | Target        | What it creates                      |
| --------------------- | ----------- | ------------- | ------------------------------------ |
| `audit-node`          | `npm audit` | order-service | Security issue → assigned to Copilot |
| `audit-python`        | `pip-audit` | ai-service    | Security issue → assigned to Copilot |
| `test-coverage-check` | file search | all services  | Quality issue → assigned to Copilot  |

> **Note**: The workflow is available in `checkpoint/module-4`. You can either paste it manually or merge the checkpoint branch.

The YAML content is in the checkpoint branch. To use it:

**Option A — Merge checkpoint** (recommended):

1. Go to your fork → Pull requests → New pull request
2. Base: `main` ← Compare: `checkpoint/module-4`
3. Create PR → Merge it

**Option B — Create manually**: Go to the checkpoint branch on GitHub to view the file content: `https://github.com/<you>/aks-store-demo/blob/checkpoint/module-4/.github/workflows/security-audit-autofix.yml`

---

## How the Copilot Assignment Works

The workflow uses a two-step pattern:

**Step 1**: Create the issue via `actions/github-script` (uses `GITHUB_TOKEN`)

**Step 2**: Assign Copilot via `gh api` (uses `PAT_TOKEN` — your personal token with Copilot entitlement)

```yaml
- name: Assign Copilot to issue
  env:
    GH_TOKEN: ${{ secrets.PAT_TOKEN }}
  run: |
    # Try multiple known Copilot assignee names
    for ASSIGNEE in "copilot-swe-agent[bot]" "copilot-swe-agent" "Copilot" "copilot"; do
      gh api "repos/$REPO/issues/$ISSUE_NUMBER/assignees" \
        --method POST \
        --input - <<< "{\"assignees\":[\"$ASSIGNEE\"]}"
      # Verify the assignment stuck
      CURRENT=$(gh api "repos/$REPO/issues/$ISSUE_NUMBER" --jq '[.assignees[].login] | join(",")')
      if echo "$CURRENT" | grep -qi "copilot"; then
        echo "✅ Assigned to Copilot"
        break
      fi
    done
```

Key points:

- `GITHUB_TOKEN` _cannot_ assign Copilot — it lacks your user's Copilot entitlement
- `PAT_TOKEN` carries your identity, so the GitHub API recognizes Copilot as a valid assignee
- The loop tries multiple names because the Copilot bot's login varies

---

## After Committing / Merging

1. Go to your fork's **Actions** tab
2. Click **"Security Audit → Auto-Create Issues → Assign to Copilot"** in the left sidebar
3. Click **"Run workflow"** → select `main` branch → **"Run workflow"**
4. Wait ~2 minutes for the jobs to complete
5. Go to **Issues** tab — you should see new issues **assigned to Copilot** with "Copilot is working" badge
6. Go to **Pull Requests** tab — within ~5 minutes, Copilot will create PRs from those issues
