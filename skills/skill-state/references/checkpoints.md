# Checkpoint helper

Python 3.9+ with its standard `sqlite3` module; no network, model API, shell runner,
third-party packages or API key. Resolve `scripts/checkpoint.py` relative to the
loaded skill directory, not to the project working directory. On Windows use an
available `python` or `py -3`; actual Windows execution has not been validated.

## Choose identity and storage

Use the canonical absolute project directory and the current Codex task ID when
available. Otherwise assign one stable, explicit task label and retain it in the
handoff; do not derive identity from the changing current directory.

Keep the project's existing task-specific checkpoint if it already has one; do not
create a second competing source. Otherwise the helper defaults to
`~/.local/state/skill-state/native/PROJECT_HASH/TASK_HASH-RUN_UUID/state.sqlite3`.
`init` always creates a new private run and never resumes, overwrites or clears an
old one. `show`, `update` and `verify` require the returned canonical `--run` path.
There is intentionally no automatic "latest task" selection.

Follow host filesystem permissions. If the default root is unavailable, use
`--root` with an authorized task-specific directory or a directory created using
`mktemp -d` in allowed temporary storage. Identify temporary storage as such in
handoffs; it is not guaranteed durable. Do not install dependencies or escalate
merely to save a checkpoint when the existing project format suffices.

## One complete example

Replace the example paths and identity with the current task. First initialize:

```sh
python3 /absolute/skill-state/scripts/checkpoint.py init \
  --project /absolute/project --task-id fix-parser-1 \
  --goal 'Correct parser behavior' --scope 'Local parser source and tests only' \
  --criterion 'Parser regression suite passes'
```

Retain the returned `run`, `identity` and `revision`. `init`/`show` print bounded
state; `verify` checks the full journal but prints only identity, revision, digest
and active-state byte count. After **actually** running the suite, create a UTF-8
patch file using the host's normal editing tool, for example:

```json
{
  "phase": "verify",
  "facts": {"changed_files": "src/parser.py; tests/test_parser.py"},
  "completed": ["Parser fix implemented and regression tests executed"],
  "evidence": [{
    "id": "parser-tests",
    "source": "/absolute/task-artifacts/parser-tests.txt",
    "observed_at": "2026-09-05T10:00:00Z"
  }],
  "checks": [{
    "criterion": "Parser regression suite passes",
    "status": "passed",
    "evidence_ids": ["parser-tests"]
  }],
  "next_step": "Inspect final diff for unrelated changes"
}
```

Use the real timestamp and inspected artifact, not the example claim. Apply it:

```sh
python3 /absolute/skill-state/scripts/checkpoint.py update \
  --project /absolute/project --task-id fix-parser-1 \
  --run /absolute/returned-run --expected-revision 0 \
  --patch-file /absolute/task-artifacts/patch.json
```

At resume or handoff:

```sh
python3 /absolute/skill-state/scripts/checkpoint.py verify \
  --project /absolute/project --task-id fix-parser-1 --run /absolute/returned-run
python3 /absolute/skill-state/scripts/checkpoint.py show \
  --project /absolute/project --task-id fix-parser-1 --run /absolute/returned-run
```

Do not run both on every tool call: `show` also verifies internally. Complete with
`phase: "done"`, empty `pending`, `blockers`, `next_step`, and all criteria passed
with evidence, only after inspecting all remaining acceptance conditions.

## Contract and recovery

- `goal`, `scope`, `criteria` are immutable for a run. A materially changed task
  needs a new run and revalidated authority, not an amended scope hidden in state.
- Mutable fields: `phase` (`inspect/work/verify/blocked/done`), string map `facts`,
  string lists `decisions/completed/pending/blockers`, `evidence`, `checks`,
  `next_step`. Record changed files in facts and detailed diffs as evidence.
- RFC 7396 patches merge objects, replace arrays and delete keys with `null`.
  Required top-level fields cannot be deleted. Unknown/duplicate/unsafe JSON keys,
  non-finite numbers, malformed timestamps and states over 8192 UTF-8 bytes fail.
- Checks reference exact criteria; status is `passed/failed/not_run`.
  A running test remains `not_run` with its job ID and next poll in pending work.
  Each passed check requires at least one existing evidence ID. Evidence contains
  `id/source/observed_at`, with optional content `sha256`.
- SQLite transaction + expected revision protects against partial commits and
  concurrent lost updates. A no-op patch creates no extra revision. A conflict
  requires a fresh read and reconciliation with actual work, not automatic replay.
- Storage is local, not a cross-machine synchronization protocol. Keep it on a
  local filesystem. Backup a closed database or use SQLite's backup API; don't
  copy it while another process is writing. No automatic deletion/rotation.
- Hash-linked revisions detect accidental edits, not malicious rewriting or tail
  removal by the file owner. `verify` does not open evidence, prove its freshness,
  measure tokens, or authorize actions. Inspect source evidence separately.
- The helper cannot atomically commit an external tool's effects with its database.
  After a crash, examine files/jobs before repeating any action. For irreversible
  effects use the real service's idempotency/reconciliation procedure.
- Runtime validation/storage errors exit 2 with bounded JSON on stderr. Invalid
  CLI arguments exit 2 with standard argparse usage text. Do not delete a corrupt run or
  overwrite someone else's state to make validation pass; retain it for diagnosis.
