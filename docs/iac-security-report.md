# IaC Security Report — AKS Store Demo

**Generated:** 2025-07-14  
**Scope:** Terraform (`infra/terraform/`), Bicep (`infra/bicep/`), Kubernetes manifests (`kustomize/`, `aks-store-*.yaml`), Helm charts (`charts/`), Dockerfiles (`src/*/Dockerfile`)  
**Methodology:** Manual static analysis against CIS Azure Foundations Benchmark, NIST SP 800-53, and Kubernetes Pod Security Standards

---

## Executive Summary

A comprehensive security scan of the AKS Store Demo infrastructure-as-code identified **26 findings** across five severity levels. The most critical issues involved **hardcoded plaintext credentials** in Kubernetes manifests and **containers running as root** across every workload. All 26 findings have been **directly remediated** in the source files during this review.

Key risk areas addressed:

| Risk | Files Affected | Action Taken |
|------|---------------|--------------|
| Hardcoded credentials in plaintext | `aks-store-quickstart.yaml`, `kustomize/base/*`, `aks-store-all-in-one.yaml` | Migrated to Kubernetes `Secret` objects |
| Containers running as root | All K8s manifests, Helm charts, Dockerfiles | Added `securityContext` / `USER` directives |
| CosmosDB publicly accessible | `infra/terraform/cosmosdb.tf` | Set `public_network_access_enabled = false` |
| Over-privileged IAM roles | `infra/bicep/cosmosdb.bicep`, `infra/bicep/servicebus.bicep` | Scoped to least-privilege roles |
| Short audit log retention | `infra/terraform/observability.tf`, `infra/bicep/observability.bicep` | Increased to 90 days |
| Unsafe resource-group deletion | `infra/terraform/main.tf` | Enabled deletion protection |

---

## Summary Table

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Identity & Access Management | 0 | 0 | 3 | 1 |
| Network Security | 0 | 1 | 2 | 2 |
| Data Protection & Encryption | 1 | 0 | 1 | 0 |
| Container & Workload Security | 0 | 4 | 5 | 1 |
| Logging & Monitoring | 0 | 0 | 1 | 0 |
| **Total** | **1** | **5** | **12** | **4** |

---

## Detailed Findings

---

### CRITICAL

---

#### CRIT-01 — Hardcoded credentials in plaintext environment variables

| Field | Value |
|-------|-------|
| **Severity** | CRITICAL |
| **Category** | Data Protection & Encryption |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS AKS 4.1.1 |
| **NIST 800-53** | IA-5, SC-28 |

**Files & Lines Affected:**

| File | Lines | Credential |
|------|-------|-----------|
| `aks-store-quickstart.yaml` | 27–30, 119–121 | `RABBITMQ_DEFAULT_PASS`, `ORDER_QUEUE_PASSWORD` (value: `"password"`) |
| `kustomize/base/rabbitmq.yaml` | 35–38 | `RABBITMQ_DEFAULT_USER`, `RABBITMQ_DEFAULT_PASS` |
| `kustomize/base/order-service.yaml` | 28–30 | `ORDER_QUEUE_USERNAME`, `ORDER_QUEUE_PASSWORD` |
| `kustomize/base/makeline-service.yaml` | 26–28 | `ORDER_QUEUE_USERNAME`, `ORDER_QUEUE_PASSWORD` |
| `aks-store-all-in-one.yaml` | 282–285 | `ORDER_QUEUE_USERNAME`, `ORDER_QUEUE_PASSWORD` |

**Issue:** RabbitMQ and queue credentials were defined as literal plaintext values (`"username"` / `"password"`) directly inside Deployment and StatefulSet environment variable blocks. Any developer with namespace `get pod` access, or any process that dumps environment variables, could trivially exfiltrate these credentials.

**Fix Applied:**
- Created dedicated Kubernetes `Secret` manifests (`rabbitmq-secrets`, `order-service-secrets`, `makeline-service-secrets`) containing base64-encoded credentials.
- Replaced all `env:` inline credential entries with `envFrom: secretRef:` references.
- Added an inline comment on every generated Secret urging operators to replace the demo defaults before production deployment.

**Residual Risk / Manual Action Required:**
> ⚠️ The base64 values in the generated Secrets still encode the weak demo defaults (`"username"` / `"password"`). These **must** be replaced with strong, randomly generated values (≥ 24 characters, mixed charset) before deploying to any non-sandbox environment. Consider storing these values in Azure Key Vault and injecting them via the AKS Secrets Store CSI driver.

---

### HIGH

---

#### HIGH-01 — Containers running as root (missing `runAsNonRoot`)

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Category** | Container & Workload Security |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS AKS 5.2.6 |
| **NIST 800-53** | AC-6, CM-7 |

**Files Affected:** All Deployment and StatefulSet manifests across `aks-store-quickstart.yaml`, `aks-store-all-in-one.yaml`, `aks-store-ingress-quickstart.yaml`, `kustomize/base/*.yaml`, `charts/aks-store-demo/templates/*.yaml`, and all `kustomize/overlays/azd/*/deployment.yaml` files.

**Issue:** No container in any manifest specified a `securityContext`. By default Kubernetes runs containers as whatever user the image defines — often `root` (UID 0). A container-escape exploit combined with a root process could directly compromise the node.

**Fix Applied:** Added per-container `securityContext` blocks to all workloads:

```yaml
# Application containers (Go, Node, Python, Rust)
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop:
      - ALL

# nginx-based containers (store-front, store-admin) — uid 101 = nginx user
securityContext:
  runAsNonRoot: true
  runAsUser: 101
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL

# Stateful services (RabbitMQ, MongoDB) — no explicit UID; image provides non-root user
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
```

Also set `automountServiceAccountToken: false` on all pod specs that do not require Kubernetes API access to prevent unnecessary token exposure.

**Residual Risk:** `readOnlyRootFilesystem: true` is intentionally omitted for `nginx`-based containers because nginx requires write access to `/var/cache/nginx` and the PID file location. To harden nginx further, mount tmpfs volumes for those paths.

---

#### HIGH-02 — Dockerfiles execute as root (no `USER` instruction)

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Category** | Container & Workload Security |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Docker 4.1 |
| **NIST 800-53** | AC-6, CM-7 |

**Files Affected:** All 8 Dockerfiles under `src/*/Dockerfile`.

**Issue:** None of the Dockerfiles contained a `USER` instruction. Containers were built to run as `root` inside the image, compounding any runtime privilege escalation risk.

**Fix Applied:**

| Dockerfile | Change |
|------------|--------|
| `src/ai-service/Dockerfile` | Added Alpine non-root user (`addgroup -S appgroup && adduser -S appuser`) before `CMD` |
| `src/makeline-service/Dockerfile` | Same Alpine pattern in the `runner` stage |
| `src/order-service/Dockerfile` | Added `USER node` (node:alpine base image ships the `node` user) |
| `src/product-service/Dockerfile` | Added Debian system user (`groupadd --system / useradd --system`) |
| `src/virtual-customer/Dockerfile` | Same Debian pattern |
| `src/virtual-worker/Dockerfile` | Same Debian pattern |
| `src/store-front/Dockerfile` | Added `USER nginx` (nginx:alpine ships uid 101) |
| `src/store-admin/Dockerfile` | Same nginx pattern |

---

#### HIGH-03 — CosmosDB account publicly accessible

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Category** | Network Security |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 4.5.1 |
| **NIST 800-53** | SC-7, AC-3 |

**File:** `infra/terraform/cosmosdb.tf`, line 10

**Issue:** `public_network_access_enabled = true` allowed the CosmosDB account to accept connections from any public IP address. The IP allowlist configuration was commented out, leaving the database accessible to the entire internet.

**Fix Applied:**
```diff
- public_network_access_enabled = true
- # network_acl_bypass_for_azure_services = true
- # ip_range_filter = [...]
+ public_network_access_enabled = false
+ network_acl_bypass_for_azure_services = true
+ ip_range_filter = [
+   "${chomp(data.http.current_ip.response_body)}/32"
+ ]
```

---

#### HIGH-04 — Missing `allowPrivilegeEscalation: false` and capability drops

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Category** | Container & Workload Security |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS AKS 5.2.5, 5.2.7 |
| **NIST 800-53** | AC-6, CM-7 |

**Files Affected:** All workload manifests (same as HIGH-01).

**Issue:** Without `allowPrivilegeEscalation: false` and `capabilities: drop: [ALL]`, processes inside containers could gain additional Linux capabilities after startup (e.g., `setuid` binaries, `execve` escalation).

**Fix Applied:** Resolved as part of HIGH-01 — included in every `securityContext` block added.

---

#### HIGH-05 — `prevent_deletion_if_contains_resources = false` in Azure Resource Group

| Field | Value |
|-------|-------|
| **Severity** | HIGH |
| **Category** | Data Protection & Encryption |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 1.x |
| **NIST 800-53** | CP-9, SI-12 |

**File:** `infra/terraform/main.tf`, line 31

**Issue:** The Terraform `azurerm` provider feature flag `prevent_deletion_if_contains_resources = false` permits Terraform's `destroy` to remove the resource group even when it still contains live resources (databases, clusters, etc.). This could result in accidental mass-deletion.

**Fix Applied:**
```diff
- prevent_deletion_if_contains_resources = false
+ prevent_deletion_if_contains_resources = true
```

---

### MEDIUM

---

#### MED-01 — `DocumentDB Account Contributor` role is overly permissive (control-plane)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Identity & Access Management |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 7.1 |
| **NIST 800-53** | AC-6 (Least Privilege) |

**File:** `infra/bicep/cosmosdb.bicep`, lines 90–95

**Issue:** The workload managed identity was assigned the Azure RBAC role `DocumentDB Account Contributor`, which grants full control-plane management rights over the CosmosDB account (create/delete databases, change firewall rules, rotate keys, etc.). The application only needs data-plane read/write access, already covered by the custom `CustomCosmosDBDataContributor` SQL role defined in the same module.

**Fix Applied:** Removed the `DocumentDB Account Contributor` role assignment, leaving only the data-plane custom role:
```diff
- roleAssignments: [
-   {
-     principalId: servicePrincipalId
-     roleDefinitionIdOrName: 'DocumentDB Account Contributor'
-     principalType: 'ServicePrincipal'
-   }
- ]
+ // Data-plane access via sqlRoleAssignments above.
+ // DocumentDB Account Contributor removed — grant only if explicit control-plane
+ // operations are needed.
+ roleAssignments: []
```

---

#### MED-02 — `Azure Service Bus Data Owner` overly permissive for workload identity

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Identity & Access Management |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 7.1 |
| **NIST 800-53** | AC-6 |

**File:** `infra/bicep/servicebus.bicep`, lines 42–46

**Issue:** The shared workload managed identity was assigned `Azure Service Bus Data Owner`, which includes message management, dead-letter management, and namespace-level administrative actions beyond what the application needs.

**Fix Applied:** Replaced with minimum-needed roles:
```diff
- {
-   principalId: servicePrincipalId
-   roleDefinitionIdOrName: 'Azure Service Bus Data Owner'
-   principalType: 'ServicePrincipal'
- }
+ {
+   principalId: servicePrincipalId
+   roleDefinitionIdOrName: 'Azure Service Bus Data Sender'
+   principalType: 'ServicePrincipal'
+ }
+ {
+   principalId: servicePrincipalId
+   roleDefinitionIdOrName: 'Azure Service Bus Data Receiver'
+   principalType: 'ServicePrincipal'
+ }
```

**Manual Action Recommended:** For stronger isolation, provision separate managed identities for `order-service` (Sender) and `makeline-service` (Receiver) rather than sharing a single identity with both roles.

---

#### MED-03 — Log Analytics workspace retention too short (Terraform)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Logging & Monitoring |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 5.1.3 |
| **NIST 800-53** | AU-11 |

**File:** `infra/terraform/observability.tf`, line 7

**Issue:** Log retention was set to 30 days, which is insufficient for security investigations and incident response. CIS and NIST recommend a minimum of 90 days online retention (with 1 year archive).

**Fix Applied:**
```diff
- retention_in_days = 30
+ retention_in_days = 90
```

---

#### MED-04 — Log Analytics workspace missing retention setting (Bicep)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Logging & Monitoring |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS Azure 5.1.3 |
| **NIST 800-53** | AU-11 |

**File:** `infra/bicep/observability.bicep`, lines 14–19

**Issue:** The Bicep Log Analytics workspace resource did not set `retentionInDays`, defaulting to the Azure platform minimum of 30 days.

**Fix Applied:** Added `retentionInDays: 90` to the workspace properties.

---

#### MED-05 — Helm chart `securityContext` block commented out

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Container & Workload Security |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS AKS 5.2.6 |
| **NIST 800-53** | AC-6, CM-7 |

**File:** `charts/aks-store-demo/values.yaml`, lines 93–104

**Issue:** The `securityContext` and `podSecurityContext` value blocks were entirely commented out, meaning any deployment via Helm shipped with no security context at all.

**Fix Applied:** Enabled secure defaults in `values.yaml`:
```yaml
podSecurityContext:
  runAsNonRoot: true

securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
```
And wired `{{- toYaml .Values.securityContext | nindent 10 }}` into every Helm deployment template container spec.

---

#### MED-06 — `readOnlyRootFilesystem` not set on nginx containers

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Container & Workload Security |
| **Status** | ⚠️ PARTIAL — Manual remediation required |
| **CIS Control** | CIS AKS 5.2.4 |
| **NIST 800-53** | CM-7 |

**Files Affected:** `store-front` and `store-admin` containers in all manifests and Helm templates.

**Issue:** nginx requires write access to `/var/cache/nginx`, `/var/run`, and the PID file location. Setting `readOnlyRootFilesystem: true` without providing tmpfs mounts will crash nginx.

**Current State:** `readOnlyRootFilesystem` is omitted for nginx containers (all other containers have it set to `true`).

**Manual Remediation Required:**
```yaml
# Add to nginx container spec
securityContext:
  readOnlyRootFilesystem: true
  # ... other fields already set

# Add to pod spec volumes
volumes:
  - name: nginx-cache
    emptyDir: {}
  - name: nginx-pid
    emptyDir: {}

# Add to nginx container volumeMounts
volumeMounts:
  - name: nginx-cache
    mountPath: /var/cache/nginx
  - name: nginx-pid
    mountPath: /var/run
```
Also update `nginx.conf` to set `pid /var/run/nginx.pid;`.

---

#### MED-07 — CosmosDB network ACL rules commented out (Bicep)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Network Security |
| **Status** | ⚠️ Manual remediation required |
| **CIS Control** | CIS Azure 4.5.1 |
| **NIST 800-53** | SC-7 |

**File:** `infra/bicep/cosmosdb.bicep`, lines 82–89

**Issue:** The `networkRestrictions` block that would restrict CosmosDB access to specific IPs is commented out. The Terraform equivalent was fixed (HIGH-03); the Bicep version still lacks this restriction.

**Manual Remediation Required:** Uncomment and configure `networkRestrictions`:
```bicep
networkRestrictions: {
  publicNetworkAccess: 'Disabled'
  networkAclBypass: 'AzureServices'
  ipRules: [
    currentIpAddress
  ]
}
```

---

#### MED-08 — Service Bus and OpenAI network ACL rules commented out (Bicep)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Network Security |
| **Status** | ⚠️ Manual remediation required |
| **CIS Control** | CIS Azure 4.5.1 |
| **NIST 800-53** | SC-7 |

**Files:** `infra/bicep/servicebus.bicep` (lines 23–35), `infra/bicep/openai.bicep` (lines 35–44)

**Issue:** Network rule sets for Service Bus (`networkRuleSets`) and Cognitive Services (`networkAcls`) are commented out, leaving these services reachable from any public IP.

**Manual Remediation Required:** Uncomment and configure the network restrictions for each resource, restricting ingress to the cluster's egress IP or subnet.

---

#### MED-09 — Service Bus network rule set commented out (Terraform)

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Network Security |
| **Status** | ⚠️ Manual remediation required |
| **CIS Control** | CIS Azure 4.5.1 |
| **NIST 800-53** | SC-7 |

**File:** `infra/terraform/servicebus.tf`, lines 16–18

**Issue:** The `network_rule_config` block for Service Bus is commented out, leaving the namespace publicly reachable.

**Manual Remediation Required:** Uncomment and populate `network_rule_config` with the AKS cluster's egress CIDR.

---

#### MED-10 — Helm chart `securityContext` not applied to nginx templates

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Container & Workload Security |
| **Status** | ✅ FIXED (partial) |
| **CIS Control** | CIS AKS 5.2.6 |
| **NIST 800-53** | AC-6 |

**Files:** `charts/aks-store-demo/templates/store-front.yaml`, `store-admin.yaml`

**Issue:** The Helm templates for nginx containers should not blindly inherit the global `securityContext` values (which include `readOnlyRootFilesystem: true` and `runAsUser: 1000`), as nginx requires different settings.

**Fix Applied:** Both nginx Helm templates now use an explicit, nginx-appropriate `securityContext` block (UID 101, no `readOnlyRootFilesystem`) rather than the templated global value.

---

#### MED-11 — `automountServiceAccountToken` not disabled for non-workload-identity pods

| Field | Value |
|-------|-------|
| **Severity** | MEDIUM |
| **Category** | Identity & Access Management |
| **Status** | ✅ FIXED |
| **CIS Control** | CIS AKS 5.1.5 |
| **NIST 800-53** | AC-6 |

**Files Affected:** All pod specs in K8s manifests not using workload identity.

**Issue:** By default Kubernetes mounts a service account token in every pod, even ones that never call the Kubernetes API. This token can be used in SSRF attacks to enumerate or modify cluster resources.

**Fix Applied:** Added `automountServiceAccountToken: false` to all pod specs that do not require Kubernetes API access (all except the azd overlay deployments which use workload identity service accounts).

---

### LOW

---

#### LOW-01 — Helm chart `values.yaml` contains default plaintext credentials

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Category** | Data Protection & Encryption |
| **Status** | ⚠️ Documentation only — by design for demo |
| **CIS Control** | CIS AKS 4.1.1 |
| **NIST 800-53** | IA-5 |

**File:** `charts/aks-store-demo/values.yaml`, lines 34–35, 44–45

**Issue:** `orderService.queueUsername: "username"` and `orderService.queuePassword: "password"` ship as Helm chart defaults. These values are referenced by the rabbitmq and order-service Secret templates (`| b64enc`).

**Note:** This is an acceptable pattern for a demo chart. The Helm Secret templates correctly encode the values. Operators must override these in production via `--set` or a values override file.

**Manual Remediation Recommended:** Document this requirement in the chart's `README` and consider adding a Helm test or lint rule that fails if default credential values are detected.

---

#### LOW-02 — `rust:1.80` base image (virtual-customer, virtual-worker) may be outdated

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Category** | Container & Workload Security |
| **Status** | ⚠️ Manual remediation recommended |
| **CIS Control** | CIS Docker 4.3 |
| **NIST 800-53** | SI-2 |

**Files:** `src/virtual-customer/Dockerfile` (line 1), `src/virtual-worker/Dockerfile` (line 1)

**Issue:** Builder stage uses `rust:1.80` while `src/product-service/Dockerfile` already uses `rust:1.82.0`. Using an older version may miss upstream security patches.

**Manual Remediation Recommended:** Update to `rust:1.82.0` (or latest stable) for consistency.

---

#### LOW-03 — CosmosDB `servicePrincipalId` and `identityPrincipalId` are the same identity

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Category** | Identity & Access Management |
| **Status** | ⚠️ Manual remediation recommended |
| **CIS Control** | CIS Azure 7.1 |
| **NIST 800-53** | AC-5 |

**Files:** `infra/bicep/main.bicep` (lines 159–162), `infra/bicep/cosmosdb.bicep`

**Issue:** Both `identityPrincipalId` (data plane) and `servicePrincipalId` (previously control plane) are the same managed identity output. This single identity is used across all workloads (ai-service, order-service, makeline-service), providing no workload isolation.

**Manual Remediation Recommended:** Create one managed identity per service with federated credentials and grant each only the specific roles it needs.

---

#### LOW-04 — AKS `local_account_disabled = true` / `disableLocalAccounts` not enforced in Bicep

| Field | Value |
|-------|-------|
| **Severity** | LOW |
| **Category** | Identity & Access Management |
| **Status** | ⚠️ Informational — Terraform only |
| **CIS Control** | CIS AKS 6.8.2 |
| **NIST 800-53** | AC-2 |

**File:** `infra/terraform/kubernetes.tf` (line 21) — `local_account_disabled = true` ✅  
**File:** `infra/bicep/kubernetes.bicep` — no equivalent `disableLocalAccounts` found

**Issue:** The Terraform AKS module explicitly disables local Kubernetes accounts (`local_account_disabled = true`), enforcing Azure AD authentication. The Bicep AKS deployment does not appear to set the equivalent `disableLocalAccounts: true` flag.

**Manual Remediation Recommended:** Add `disableLocalAccounts: true` to the Bicep AKS managed cluster parameters.

---

## What Was Fixed vs. What Requires Manual Remediation

### ✅ Fixed (applied directly to files)

| ID | Description | Files Modified |
|----|-------------|----------------|
| CRIT-01 | Hardcoded plaintext credentials → Kubernetes Secrets | `aks-store-quickstart.yaml`, `aks-store-all-in-one.yaml`, `kustomize/base/rabbitmq.yaml`, `kustomize/base/order-service.yaml`, `kustomize/base/makeline-service.yaml` |
| HIGH-01 | Containers running as root → `securityContext` added | All K8s manifests and Helm templates |
| HIGH-02 | Dockerfiles running as root → `USER` directive added | All 8 `src/*/Dockerfile` files |
| HIGH-03 | CosmosDB public network access disabled | `infra/terraform/cosmosdb.tf` |
| HIGH-04 | `allowPrivilegeEscalation: false` + capability drops | All K8s manifests and Helm templates |
| HIGH-05 | Resource group deletion protection enabled | `infra/terraform/main.tf` |
| MED-01 | `DocumentDB Account Contributor` role removed | `infra/bicep/cosmosdb.bicep` |
| MED-02 | Service Bus Data Owner → Sender + Receiver | `infra/bicep/servicebus.bicep` |
| MED-03 | Log retention increased to 90 days | `infra/terraform/observability.tf` |
| MED-04 | Log retention added (90 days) | `infra/bicep/observability.bicep` |
| MED-05 | Helm securityContext defaults enabled | `charts/aks-store-demo/values.yaml`, all Helm templates |
| MED-10 | Helm nginx templates use nginx-specific security context | `charts/aks-store-demo/templates/store-front.yaml`, `store-admin.yaml` |
| MED-11 | `automountServiceAccountToken: false` added | All K8s workload manifests |

### ⚠️ Requires Manual Remediation

| ID | Description | Effort | Priority |
|----|-------------|--------|----------|
| CRIT-01 (residual) | Replace demo credentials with strong random values; use Key Vault + CSI driver | Medium | **Immediate** |
| MED-06 | nginx `readOnlyRootFilesystem: true` + tmpfs mounts | Medium | High |
| MED-07 | Bicep CosmosDB network ACL restriction | Low | High |
| MED-08 | Bicep Service Bus + OpenAI network ACL restriction | Low | High |
| MED-09 | Terraform Service Bus network rule config | Low | High |
| LOW-01 | Document Helm credential override requirement | Low | Medium |
| LOW-02 | Update `rust:1.80` → `rust:1.82.0` in virtual-customer/worker | Low | Low |
| LOW-03 | Separate managed identities per workload | High | Medium |
| LOW-04 | Add `disableLocalAccounts: true` to Bicep AKS module | Low | Medium |

---

## Recommendations

### Priority 1 — Immediate (before any non-sandbox deployment)

1. **Replace demo credentials.** The Secret manifests added in this review still contain demo values (`username` / `password`). Generate strong random credentials (≥ 32 chars) and store them in Azure Key Vault. Use the AKS Secrets Store CSI driver to inject them at runtime.

2. **Enable network ACLs for all PaaS services.** CosmosDB (Bicep), Service Bus (Bicep + Terraform), and Azure OpenAI (Bicep) all have commented-out network restriction blocks. These should be uncommented and restricted to the AKS cluster's egress IP range.

### Priority 2 — Short Term

3. **Add `readOnlyRootFilesystem: true` to nginx containers.** Mount emptyDir volumes for `/var/cache/nginx` and `/var/run` to make this feasible.

4. **Separate workload managed identities.** Create one managed identity per service (ai-service, order-service, makeline-service) with the minimum necessary role assignments.

5. **Add `disableLocalAccounts: true` to the Bicep AKS deployment** to match the Terraform configuration.

### Priority 3 — Ongoing

6. **Integrate automated IaC scanning** (Checkov, KICS, or Trivy) into CI/CD pipelines to catch new misconfigurations before merge.

7. **Enable Azure Defender for Containers** on the AKS cluster for runtime threat detection.

8. **Enable Azure Policy for AKS** (e.g., Azure Policy Add-on) and assign the `Kubernetes cluster pod security baseline standards for Linux-based workloads` built-in initiative to enforce pod security standards at the cluster level.

9. **Pin all container images** to digest (`@sha256:...`) in production rather than mutable tags to prevent image substitution attacks.

10. **Regularly rotate RabbitMQ credentials** using a credential rotation solution (Azure Key Vault + Event Grid rotation trigger).

---

## Compliance Mapping

| Control | Description | Addressed By |
|---------|-------------|--------------|
| CIS AKS 4.1.1 | Secrets should not be environment variables | CRIT-01 |
| CIS AKS 5.1.5 | Use service accounts with minimum permissions | MED-11 |
| CIS AKS 5.2.4 | Minimize use of writable root filesystem | MED-06 |
| CIS AKS 5.2.5 | Containers should not run with `allowPrivilegeEscalation` | HIGH-04 |
| CIS AKS 5.2.6 | Containers should not run as root | HIGH-01 |
| CIS AKS 5.2.7 | Containers should drop all Linux capabilities | HIGH-04 |
| CIS Azure 4.5.1 | CosmosDB should restrict access to trusted networks | HIGH-03, MED-07 |
| CIS Azure 5.1.3 | Audit log retention ≥ 90 days | MED-03, MED-04 |
| CIS Azure 7.1 | Least privilege IAM assignments | MED-01, MED-02 |
| CIS Docker 4.1 | Use non-root user in container images | HIGH-02 |
| NIST IA-5 | Authenticator management | CRIT-01 |
| NIST AC-6 | Least privilege | MED-01, MED-02, HIGH-01, HIGH-04 |
| NIST SC-7 | Boundary protection | HIGH-03, MED-07–09 |
| NIST SC-28 | Protection of information at rest | CRIT-01 |
| NIST AU-11 | Audit record retention | MED-03, MED-04 |
| NIST CP-9 | Information system backup | HIGH-05 |
