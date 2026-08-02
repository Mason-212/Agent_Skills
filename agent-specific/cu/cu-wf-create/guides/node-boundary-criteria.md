# Node Boundary Criteria

When designing workflows, use these 6 criteria to determine node boundaries:

## 1. Distinct Responsibility

**Rule:** Different "job" (fetch vs transform vs notify)

**Example:**
- Fetcher node: Calls GitHub API for PRs
- Processor node: Aggregates PR data
- Different jobs → separate nodes

## 2. Data Handoff

**Rule:** Node A outputs artifact, Node B consumes it

**Example:**
- Analyzer outputs findings.json
- Reporter reads findings.json
- Clear handoff → separate nodes

## 3. Different Tools

**Rule:** Read-only vs writes vs APIs vs MCP servers

**Example:**
- Analyzer needs: Bash, Read, Grep (read-only)
- Reporter needs: Write (writes files)
- Different tool sets → separate nodes

## 4. Independent Failure

**Rule:** Node A can fail without invalidating Node B

**Example:**
- Fetcher can fail (network error)
- Processor still valid (can retry fetch)
- Independent failure modes → separate nodes

## 5. Reusability

**Rule:** Node could be extracted for other workflows

**Example:**
- Security scanner node could be reused across workflows
- Reusable component → separate node

## 6. ⭐ Verification Gate

**Rule:** Node B independently verifies Node A achieved its goal

**Example:**
- Analyzer produces findings.json
- Reporter validates findings.json schema before writing report
- Different agent = independent verification
- Catches if analyzer crashed or output malformed

**Key insight:** Each node transition is a quality gate.

## Decision Framework

Create separate nodes when **≥ 3 criteria apply**.

Keep nodes together when:
- Tightly coupled (can't do B without A)
- No useful intermediate output
- Same failure domain

## Examples

**Good: 2-node structure**
```
analyzer → reporter

Criteria:
✓ 1. Distinct: analysis vs reporting
✓ 2. Handoff: findings.json
✓ 3. Tools: test/lint vs Write
✓ 6. Verification: reporter validates schema

Result: 4/6 criteria → separate nodes justified
```

**Bad: Single node**
```
all-in-one (analyze + report)

Criteria:
✗ No verification gate
✗ No handoff checkpoint
✗ Same agent validates its own work

Result: 0/6 criteria → should split
```
