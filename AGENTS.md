# Project objective and active workflow

The primary goal is to discover and reconstruct readable, editable C++ with
supported semantic behavior. Byte-for-byte ARM identity is optional diagnostic
evidence, not an acceptance gate or the main progress metric. Do not spend a
semantic batch rearranging expressions, adding unjustified volatile, or reverting
correct C++ solely to reproduce compiler instructions.

Continue functional implementation on `codex/semantic-equivalence-experiment`.
Locate and reuse its existing checkout with `git worktree list`; the exact-matching
checkout is a reference. Preserve existing user changes in either checkout.

## Work selection

- Follow `docs/functional-status.md`, `docs/reconstruction-milestones.md`, and
  `config/reconstruction.json` in the semantic checkout. H1 main-menu integration
  is the active functional milestone.
- `python tools/find_candidates.py` defaults to semantic discovery, including
  non-leaf functions. It prioritizes milestone dependencies and omits already
  written experimental C++ from the new-reconstruction queue.
- Use `--include-existing-candidates` to find validation/integration work.
  `--mode leaf` is optional triage, not the primary workflow.
- Choose coherent behavior and its dependencies rather than maximizing tiny
  function counts. Legacy byte-matching failures do not disqualify semantic work.

## Acceptance and evidence

- Recover contracts, types, return values, memory effects, ABI requirements,
  meaningful branches, and real caller behavior.
- Validate compiled C++ against the pinned original with contract-specific
  differential cases, boundaries, negative controls, and caller tests. Record
  partial results, faults, unresolved calls, and domain limits honestly.
- Promote supported candidates into reproducible integrated replacements and
  compare the defined original-versus-patched runtime scenario. Static candidate
  presence, size thresholds, and isolated passes are not whole-game equivalence.
- Keep original inputs intact. Exact ledger labels must remain truthful: never
  call differing bytes `matching`. Experimental semantic evidence is separate;
  a production non-identical reconstruction uses a supported non-matching ledger
  classification plus its semantic record until reporting supports more detail.
- The historical 100% byte baseline is a recoverable reference, not a requirement
  to preserve 100% matching in every future semantic implementation.

## Efficient validation

Run focused checks while developing, then the relevant wider regression once per
coherent batch. Compiler/ABI changes require affected consumers and build checks.
Exact audits validate exact claims when those claims/tools change; they do not
approve or reject a new semantic candidate merely because its bytes differ.
Keep generated artifacts in ignored `build/` and private game inputs out of Git.
Historical exact-matching plans are superseded by this objective.

## Agentic execution

Use the coordinator-plus-bounded-subagents workflow in `docs/agent-workflow.md`
for continued semantic decompilation when independent work is available. The
coordinator may proactively delegate at most three scoped workers (or the tool's
lower available limit), using internal subagent tools and small prepared briefs.
Keep one active milestone and reuse idle agents for H1 review/dependency work.
Do not create new user-owned chats for subtasks.

The coordinator alone updates the active board selected by
`agent_workflow_board` in `config/reconstruction.json`. Check it with
`python tools/agent_workflow.py check`; use `ready` for schedulable work. Claim
one owner and exclusive files, then generate a new `prepare` packet before
launching a worker. Workers must not edit the board or shared interfaces/runners,
run canonical full builds, or control the emulator without exclusive assignment.
Use distinct build/report outputs and divide the eight-job CPU budget across
workers; do not let each worker start a default eight-job full build.

Require a structured handoff and independent review before promotion. Freeze
inputs while compiling/testing, invalidate affected evidence after shared changes,
and run one integrator-owned batch closure. A task acceptance, report `passed`
flag, or static candidate count is not proof of semantic or runtime equivalence.
