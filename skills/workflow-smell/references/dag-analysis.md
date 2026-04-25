# DAG Analysis — Pipeline Dependency Graphs

## Why it matters

The dependency graph is the skeleton of the pipeline. Smell patterns that
seem unrelated in isolation often form a coherent anti-pattern when the graph
is drawn. Always build this mentally (or literally) before issuing findings.

---

## Building the Graph

For GitLab CI:
```
nodes  = all job names
edges  = needs: declarations + implicit stage ordering
weights = estimated duration if available (allow: / timeout:)
```

For Makefiles:
```
nodes  = all targets
edges  = prerequisites listed per target
leaf   = targets with no prerequisites
root   = targets never listed as prerequisites
```

For shell scripts:
```
nodes  = functions / sourced scripts
edges  = call graph (function A calls function B)
```

---

## Structural Defects to Look For

### Orphaned Nodes
A job/target that:
- Is never referenced by `needs:` or any other job
- Is not a terminal (deploy/notify) job
- Is not a default entrypoint

**Smell**: H7 (Speculative Infrastructure) or L4 (TODO Workflow)

### Undeclared Edges
Two nodes share an artifact path or env var but no explicit dependency links them.
Running them concurrently → race condition. Running in wrong order → stale input.

**Smell**: H6 (Temporal Coupling Without Declaration)

### Long Serial Chains
A → B → C → D where B and C have no shared resource and could run in parallel.
Each adds latency to the critical path.

**Ask**: why aren't these parallel? If no good answer → flag as optimization opportunity.

### Fan-out without Fan-in
Job spawns N parallel jobs but no downstream job collects and validates all N results.
One failure in the fan-out may go undetected.

**Smell**: C1 (Silent Failure Masking) at the fan-in boundary.

### Cycles
Any path that leads back to a node already visited.
In CI: a job triggers a pipeline that re-triggers the original job.

**Smell**: C2 (Ouroboros Pipeline)

---

## Graph Notation (inline, when no diagram tool available)

```
build ──► test ──► package ──► deploy
           │
           └──► lint (parallel, no shared resources — good)

orphan_job  (no incoming or outgoing edges — investigate)
```

---

## Critical Path Analysis

1. Find the longest path from source to terminal node
2. Sum durations along that path
3. Identify which node contributes most
4. Ask: can anything on the critical path be parallelized or eliminated?

If the critical path passes through a node flagged with H1 (Wrapper Theater),
the wrapper is also adding latency with zero value.
