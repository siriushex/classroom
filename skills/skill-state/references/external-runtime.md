# External agent-loop integration: opt-in only

The native skill does not run the portable TypeScript executor or replace Codex.
Fresh state-only prompts require explicit client/runtime integration. In an
ordinary Codex task, checkpoints improve retrieval discipline but do not remove
history from the next model request. Do not claim constant prompt size.

The reviewed portable Windows 0.3.0 package is an experimental starting point, not
an approved all-project executor. Its custom native-stop patch is not an official
capability of every Codex build. A version string or successful initialize handshake
does not prove support. A fallback flag in JSON is not a resumed full-context loop.

Before integrating an external loop, require all of the following:

1. Explicit user scope for that integration, pinned binaries/source revisions,
   checksums, exact schemas, OS compatibility and a non-destructive rollback plan.
   Never replace the user's desktop runtime or import an unknown auth store.
2. Probe current App Server schemas and a sandboxed lifecycle fixture. Dynamic
   tools remain experimental. Verify the exact native-stop field, completion
   events, cancellation, approvals and hook behavior; unsupported means refuse
   that mode, not silently claim native stop. Preserve model and reasoning settings.
3. Enforce the tool boundary in the runtime, not only in a prompt. External
   callbacks need their own filesystem/network/process controls; Codex's sandbox
   does not automatically contain them. Node/Python allowlists are not sandboxes.
   Canonicalize paths, reject symlink escapes, protect sensitive files, constrain
   descendants and redirects, and avoid inheriting unnecessary credentials.
4. Bind persisted runs to project, task and immutable contracts. Use strict schemas,
   transactionally committed state plus audit, revision guards, durable action IDs
   and crash reconciliation. Do not automatically repeat an ambiguous effect.
   Multi-file rollback requires concurrency protection; independent renames are
   not a filesystem-wide atomic transaction.
5. Send the validated state on every fresh/resumed loop. Bound tool observations
   with artifact references, preserve required instructions/permissions, and
   implement an actual tested full-context fallback. Do not drop unresolved facts.
6. Validate effects independently. MCP `isError`, asynchronous job status and
   terminal test outcomes must propagate. Compilation is not test success. A
   `finish` action must not self-certify correctness; inspect the actual UI/output
   where necessary. Verify rollback instead of assuming an undo call succeeded.
7. Run paired repeated baselines with the same model, effort, tools, task,
   environment and acceptance tests. Count all input/cached/output tokens,
   retries, follow-up calls, failures and usage coverage; missing usage is unknown,
   not zero. Report money, tokens, quality and latency separately. Synthetic
   savings do not establish gains for every project or a 98% guarantee.

Official references (checked 2026-09-05):

- [App Server protocol](https://learn.chatgpt.com/docs/app-server)
- [Codex skill discovery and configuration](https://learn.chatgpt.com/docs/build-skills)

Use current local schemas first when integrating; protocol details may change.
