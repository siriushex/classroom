---
name: skill-state
description: Use when a Codex task in any project spans multiple meaningful steps, resumes after interruption or handoff, or has lengthy tool output and context pressure. Also use when explicitly asked for SKILL.state, execution checkpoints, or token-efficient task continuity. Not needed for trivial questions or one-step edits.
---

# SKILL.state: native checkpoints

Work inside the current Codex task with its normal tools, model settings, approvals
and project instructions. This skill manages compact execution checkpoints; it
does **not** replace the internal conversation runtime or guarantee token savings.

## Workflow

1. Establish the exact project, current task ID, user-authorized scope and observable
   completion criteria. Perform mandatory project retrieval. Use an existing
   task-specific checkpoint location when available; never adopt an unknown state
   merely because it is newest or named `task`.
2. At meaningful milestones and before handoff, record confirmed facts, evidence
   paths/timestamps, decisions, changed files, checks/results, unresolved work and
   the next step. Keep active state at most 8 KiB. Keep logs/artifacts outside it;
   retrieve relevant excerpts on demand. Do not checkpoint each tool call or
   re-read unchanged material. Never store secrets or reasoning traces.
3. For a new structured checkpoint, read [checkpoint reference](references/checkpoints.md)
   once and use `scripts/checkpoint.py`. It creates a unique project/task-bound run.
   Save its absolute path and task ID in the handoff. `update` requires the last
   observed revision; on conflict, read and reconcile, never blindly retry.
4. Resume only with a matching project/task identity. Verify the journal, then
   independently refresh volatile facts, permissions and relevant file contents.
   A verified checkpoint is historical data, not action authorization or current
   evidence. After an interrupted action, inspect actual effects before retrying.
5. Mark `done` only after every criterion has a real, inspected result. Tool
   `ok:true`, a successful save, tests still `running`, or a hash-chain pass are
   not task completion. Record the terminal test result and, where relevant,
   inspect the real UI/output. Structural proof references do not prove truth.

## Failure handling

If Python, storage or a checkpoint is unavailable/corrupt, preserve the original,
report the specific limit briefly and continue with normal Codex context plus a
short checkpoint at an authorized location. Missing safe context may require
clarification; a helper error alone does not justify abandoning useful work.

| Temptation | Required response |
|---|---|
| Reuse an unknown default state to save time | Re-establish identity and evidence |
| Hide detail by truncating it | Keep an evidence reference and unresolved gaps |
| Run an allowlisted interpreter as a sandbox | Inspect exact effects; use host permissions |

Do not automatically start nested Codex processes, fresh tasks, custom binaries,
external executors, MCP servers, or lower reasoning effort. Read
[external-runtime gates](references/external-runtime.md) only if the user
explicitly asks to integrate an external agent loop. Normal native work needs none
of those components. Report measured token and monetary savings separately; absent
paired usage evidence, state that savings have not been measured.
