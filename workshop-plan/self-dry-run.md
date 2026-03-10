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

### Step 7: Reset for workshop day

After testing, reset `main` to the clean state so attendees start fresh:

```powershell
# Reset main to the original clean state (before checkpoint merges)
git fetch origin
git checkout main
git reset --hard d18e1f2   # your last clean commit (with handouts, no checkpoint content)
git push origin main --force-with-lease
```

Or simpler — **just delete the fork and re-fork** from the upstream repo (which still has clean `main` + all checkpoint branches).

### What to watch for

| What                             | Expected                    | If it fails                                                            |
| -------------------------------- | --------------------------- | ---------------------------------------------------------------------- |
| Dependabot alerts appear         | Within 15-30 min            | Check Settings → Code security → Dependabot is enabled                 |
| CodeQL runs                      | Triggered by merge to main  | Check Actions tab for the CodeQL workflow run                          |
| Security audit workflow triggers | Manual trigger works        | Check Actions → workflow → "Run workflow" button visible               |
| Issues auto-created              | 2-3 issues in Issues tab    | Check workflow logs for errors (permissions, jq parsing)               |
| `copilot` assignee works         | "Copilot is working" badge  | Coding Agent must be enabled at **org level** — this is the #1 blocker |
| Copilot creates PRs              | PRs within 5-8 min of issue | Check the issue page for agent status updates                          |
| Copilot Code Review              | Review comments on PR       | Add `copilot` as reviewer manually via Reviewers dropdown              |

The single most important thing to validate: **assigning an issue to `copilot` triggers the Coding Agent**. If that doesn't work:

- Verify your Copilot plan is Pro, Pro+, Business, or Enterprise
- Verify the `PAT_TOKEN` secret is set (the workflow uses it to assign Copilot via the REST API)
- Try assigning Copilot manually from the issue UI — if it doesn't appear there, Copilot Coding Agent isn't enabled for your account
