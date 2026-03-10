### Step 1: Enable GitHub Features

Go to `https://github.com/sohamda/aks-store-demo/settings`:

1. **Settings → Actions → General** → "Allow all actions and reusable workflows" → Save
2. **Settings → Advanced Security** → Enable:
   - Dependabot alerts ✅
   - Secret scanning ✅
3. **Settings → Code security → Code scanning** → Set CodeQL to **default setup**
4. **Create a PAT_TOKEN secret** (required for Copilot assignment):
   - <https://github.com/settings/tokens> → Fine-grained → select repo
   - Permissions (all Read & Write): **Actions**, **Contents**, **Issues**, **Pull requests**
   - Generate → copy token
   - Repo → Settings → Secrets → Actions → New secret → Name: `PAT_TOKEN` → paste token
5. Verify Copilot Coding Agent is available: go to any issue → Assignees dropdown → "Copilot" should appear

### Step 2: Test Module 2 — Merge the checkpoint

On github.com:

1. Go to your repo → **Pull requests** → **New pull request**
2. Base: `main` ← Compare: `checkpoint/module-2`
3. Create PR → Merge it
4. Verify the 3 files appear on `main`: `copilot-instructions.md`, `dependabot.yml`, `codeql.yml`
5. **Wait ~15-30 min** — Dependabot will start creating alerts and PRs, CodeQL will run on the merge commit

### Step 3: Test Module 3 — Check DevSecOps results

After 15-30 min:

1. **Security tab → Dependabot alerts** — should show vulnerability findings
2. **Security tab → Code scanning** — CodeQL results should appear
3. **Pull requests tab** — Dependabot may have created dependency bump PRs
4. Click a CodeQL alert → look for **"Copilot Autofix"** button

### Step 4: Test Module 4 — Merge the audit workflow and trigger it

1. Go to your repo → **Pull requests** → **New pull request**
2. Base: `main` ← Compare: `checkpoint/module-4`
3. Create PR → Merge it
4. Go to **Actions** tab → **"Security Audit → Auto-Create Issues → Assign to Copilot"** → **"Run workflow"** (select `main`)
5. Wait ~2 min for it to complete
6. Go to **Issues** tab — check for auto-created issues
7. Check that issues have `copilot` as assignee and show "Copilot is working"

### Step 5: Test Module 5 — Verify Copilot creates PRs

1. Wait ~5-8 min after issues appear
2. Go to **Pull requests** tab — Copilot should open PRs from the auto-created issues
3. Open a PR → check commit history (multiple commits = agentic iterations)
4. Click **"Reviewers"** → add `copilot` → Copilot should leave review comments
5. Reply to a review comment — verify Copilot responds

### Step 6: Test manual issue assignment

1. Go to **Issues** → **New issue**
2. Title: `Add input validation to order-service POST /order`
3. Paste the body from handout-module-5-issues.md
4. Set **Assignees** → `copilot`
5. Submit → verify "Copilot is working" appears → PR opens within ~5 min

### Step 7: Test Module 6 — IaC Security Agent

1. Create the custom agent file via github.com UI:
   - "Add file" → "Create new file" → path: `.github/agents/iac-security-agent.md`
   - Paste content from `handout-module-6-iac-agent.md`
   - Commit to `main`
2. Go to **Issues** → **New issue**
3. Title: `[Security] IaC Security Scan`
4. Body:
   ```
   @copilot Use the IaCSecurityAgent to scan this repository's infrastructure code and generate a security report.

   Scan: infra/terraform/, infra/bicep/, kustomize/, charts/, src/*/Dockerfile, aks-store-*.yaml
   ```
5. Set **Assignees** → `copilot`
6. Submit → verify Copilot uses the IaCSecurityAgent to generate a security findings report
7. Check the PR — it should contain a structured security report with findings across Terraform, Bicep, K8s, Helm, and Dockerfiles

### Step 8: Test Module 7 — GitHub Agentic Workflows (gh-aw)

**Option A — CLI (if gh-aw extension is installed):**

1. Install: `gh extension install github/gh-aw`
2. Create the workflow file `.github/workflows/security-report.md` — paste content from `handout-module-7-gh-aw.md`
3. Compile: `gh aw compile` → generates `.github/workflows/security-report.lock.yml`
4. Commit and push both files
5. Set up engine secret: Settings → Secrets → `COPILOT_GITHUB_TOKEN` (use same PAT)
6. Go to **Actions** tab → **"Weekly IaC Security Report"** → **"Run workflow"**
7. Wait ~2-3 min → check **Issues** tab for a new `[security-report]` issue

**Option B — github.com Copilot Chat (no CLI needed):**

1. Open Copilot Chat on your fork
2. Enter the prompt from `handout-module-7-gh-aw.md` (Option A section)
3. Copilot will create the workflow files
4. Trigger from Actions tab

### Step 9: Reset for workshop day

After testing, reset `main` to the clean state so attendees start fresh.

**Close all test artifacts:**
```powershell
# Close all open issues
gh issue list --state open --json number --jq '.[].number' | ForEach-Object { gh issue close $_ }

# Close all open PRs
gh pr list --state open --json number --jq '.[].number' | ForEach-Object { gh pr close $_ }

# Delete copilot/* branches
git fetch --prune
git branch -r | Select-String 'origin/copilot/' | ForEach-Object { $b = $_.ToString().Trim() -replace 'origin/', ''; git push origin --delete $b }
```

**Reset main:**
```powershell
git fetch origin
git checkout main
# Find the clean commit (last commit with handouts but no checkpoint content)
git log --oneline | Select-Object -First 10
# Reset to it
git reset --hard <clean-commit-hash>
# Copy latest handouts from remote
git checkout origin/main -- workshop-plan/
git commit -m "reset main to clean state with updated workshop handouts"
git push origin main --force-with-lease
```

### What to watch for

| What                             | Expected                    | If it fails                                                                          |
| -------------------------------- | --------------------------- | ------------------------------------------------------------------------------------ |
| Dependabot alerts appear         | Within 15-30 min            | Check Settings → Advanced Security → Dependabot is enabled                           |
| CodeQL runs                      | Triggered by merge to main  | Check Actions tab for the CodeQL workflow run                                        |
| Security audit workflow triggers | Manual trigger works        | Check Actions → workflow → "Run workflow" button visible                             |
| Issues auto-created              | 2-3 issues in Issues tab    | Check workflow logs for errors (permissions, jq parsing)                             |
| `copilot` assignee works         | "Copilot is working" badge  | Needs PAT_TOKEN secret + Copilot Pro/Pro+/Business/Enterprise                        |
| Copilot creates PRs              | PRs within 5-8 min of issue | Check the issue page for agent status updates                                        |
| Copilot Code Review              | Review comments on PR       | Add `copilot` as reviewer manually via Reviewers dropdown                            |
| IaC Security Agent               | Structured security report  | Verify `.github/agents/iac-security-agent.md` is committed and agent name matches    |
| gh-aw workflow runs              | Issue created with report   | Check engine secret (`COPILOT_GITHUB_TOKEN`), verify `.lock.yml` file exists         |

The single most important thing to validate: **assigning an issue to `copilot` triggers the Coding Agent**. If that doesn't work:

- Verify your Copilot plan is Pro, Pro+, Business, or Enterprise
- Verify the `PAT_TOKEN` secret is set (the workflow uses it to assign Copilot via the REST API)
- Try assigning Copilot manually from the issue UI — if it doesn't appear there, Copilot Coding Agent isn't enabled for your account
