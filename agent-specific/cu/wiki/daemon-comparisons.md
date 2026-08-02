# Daemon Comparison Section

*Insert this as section 4.5 in appendix-concepts.md, right after section 4.4 (Workers)*

---

## 4.5. Daemon Comparisons

Understanding the CU daemon through comparisons with similar systems.

### CU Daemon vs tmux

**TLDR:** tmux = passive terminal persistence; CU daemon = active job management with state tracking, supervision, and orchestration.

| Aspect | tmux | CU Daemon |
|--------|------|-----------|
| **Primary Purpose** | Keep terminal sessions alive | Manage AI coding session lifecycle |
| **Background Execution** | ✅ Yes (detached sessions) | ✅ Yes (daemon-managed workers) |
| **State Tracking** | ❌ No (just terminal buffer) | ✅ Yes (SQLite database with full history) |
| **Lifecycle Management** | ❌ Manual (attach/detach/kill) | ✅ Automated (pause/resume/kill via API) |
| **Supervision** | ❌ No monitoring | ✅ Yes (Overseer watches for stalls, extends turns) |
| **Multiple Interfaces** | ❌ Terminal only | ✅ CLI, Mac app, Slack bot |
| **Approval Workflow** | ❌ No | ✅ Yes (auto-approve safe tools, escalate risky ones) |
| **Orchestration** | ❌ No | ✅ Yes (multi-step workflows, schedules) |
| **Isolation** | ❌ Shared environment | ✅ Separate git worktrees per session |
| **API Access** | ❌ No | ✅ HTTP/REST over Unix socket |
| **History/Audit** | ❌ No persistence | ✅ All events stored, queryable |

**When tmux is enough:**
- You just need to keep a terminal alive
- No need for state tracking or management
- Simple sequential work

**When CU daemon shines:**
- Multiple concurrent AI sessions
- Need to pause/resume/monitor progress
- Want approval workflow for risky operations
- Need orchestration (plan → execute → review)
- Want Slack notifications or GUI access

---

### CU Daemon vs Spark Driver

**TLDR:** Spark driver = ephemeral job coordinator for distributed data processing; CU daemon = persistent session manager for local AI workers.

| Aspect | Spark Driver | CU Daemon |
|--------|--------------|-----------|
| **Scope** | Distributed (cluster-wide) | Local (single machine) |
| **Purpose** | Data processing coordination | AI session lifecycle management |
| **Lifetime** | One job = one driver (ephemeral) | Persistent across many sessions |
| **Workers** | Executors on many machines | Claude processes in local worktrees |
| **State Management** | In-memory DAG scheduler | SQLite with persistent records |
| **Restart Behavior** | Driver dies = job fails | Daemon restarts = sessions resume |
| **User Interaction** | Submit job, wait for result | Interactive: pause/resume/query anytime |
| **Fault Tolerance** | Task-level retry | Session-level supervision + recovery |

**Key Difference:**

- **Spark driver:** Orchestra conductor for ONE symphony. Job ends, conductor leaves.
- **CU daemon:** Concert hall manager. Stays running, manages many performances over time.

**Similarity:** Both coordinate multiple workers and maintain execution plans.

**Why CU is different:** Spark is built for **batch data jobs** (start → compute → finish). CU is built for **interactive sessions** with long-running AI agents that need human approval, can be paused, and span days.

---

### CU Daemon vs Kubernetes Control Plane

**TLDR:** Both are persistent coordinators that spawn/monitor workloads and maintain desired state, but K8s manages containers at cluster scale while CU manages AI sessions on one machine.

| Aspect | Kubernetes Control Plane | CU Daemon |
|--------|--------------------------|-----------|
| **Architecture** | Control plane (API server, scheduler, controller manager, etcd) | Single Node.js process with SQLite |
| **Scale** | Cluster (thousands of nodes) | Single machine |
| **Workload Unit** | Pod (containerized app) | Session (Claude Code worker) |
| **Desired State** | Deployment spec → running pods | Session request → running worker |
| **State Storage** | etcd (distributed) | SQLite (local) |
| **API** | REST over TCP | REST over Unix socket |
| **Scheduling** | Multi-node bin packing | Local process spawning |
| **Lifecycle** | Pods (create/run/restart/delete) | Sessions (create/run/pause/resume/kill) |
| **Supervision** | Readiness/liveness probes, auto-restart | Overseer (stall detection, turn extension, auto-approval) |
| **Orchestration** | Deployments, StatefulSets, Jobs | Workflows (multi-step session DAGs) |

**Similarities:**

1. **Persistent coordination:** Both run continuously and manage short-lived workloads
2. **Desired state reconciliation:** User declares intent, system makes it happen
3. **API-driven:** Clients interact via REST API (kubectl ≈ cu CLI)
4. **State tracking:** Both maintain records of all workloads (etcd ≈ SQLite)
5. **Supervision:** Both watch for failures and react (K8s controller ≈ Overseer)

**Key Differences:**

- **K8s:** Built for **distributed container orchestration** at cluster scale
- **CU:** Built for **local AI session management** with human-in-the-loop approval

**Why K8s analogy fits:**

CU daemon is the closest thing to "Kubernetes for AI coding sessions" — persistent, API-driven, state-tracking, supervisor-based coordination. But local, not distributed.

---

### Summary Table

| Feature | tmux | Spark Driver | K8s Control Plane | CU Daemon |
|---------|------|--------------|-------------------|-----------|
| **Persistence** | ✅ Sessions persist | ❌ Dies with job | ✅ Always running | ✅ Always running |
| **State Tracking** | ❌ No | ⚠️ In-memory only | ✅ etcd | ✅ SQLite |
| **API Access** | ❌ No | ⚠️ Submit-only | ✅ REST | ✅ REST |
| **Supervision** | ❌ No | ⚠️ Task retry only | ✅ Controllers | ✅ Overseer |
| **Orchestration** | ❌ No | ✅ DAG execution | ✅ Deployments | ✅ Workflows |
| **Approval Flow** | ❌ No | ❌ No | ❌ No | ✅ Yes |
| **Scale** | Single machine | Cluster | Cluster | Single machine |
| **Best For** | Terminal persistence | Batch data jobs | Container orchestration | AI session management |

---

**Best Mental Model:**

> The CU daemon is like **systemd** (process lifecycle manager) + **PM2** (process supervisor) + **Jenkins** (job orchestration), but specialized for managing Claude Code AI sessions instead of generic processes.

Or simply:

> **"Kubernetes for AI coding sessions, but local instead of distributed."**

---
