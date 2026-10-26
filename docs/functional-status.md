# Editable-source reconstruction status

The active goal is readable, modifiable C++ that reproduces the game's behavior. Exact ARM output is optional diagnostic evidence, not an acceptance gate. This objective supersedes the historical byte-exact night-shift plan.

The default `python tools/find_candidates.py` command now searches for semantic reconstruction work, including non-leaf functions and already mapped assembly. Priorities are in `config/reconstruction.json`. Add `--include-existing-candidates` for validation/integration work; a candidate already written in C++ is not new reconstruction work.

## Current delivery target

Finish [H1: main-menu flow](milestones/H1-main-menu-flow.md). Choose functions and shared infrastructure because they unblock initialization, navigation, presentation, or dispatch in that milestone. Keep unrelated family expansion secondary until the integrated scenario is reproducible.

[H0](milestones/H0-reproducible-test-base.md) records batch 4 loading in Azahar and the title → Audio Settings → title smoke test, with two replacement entries observed. In [H1](milestones/H1-main-menu-flow.md), the live track callback bindings (`0x00151404` at both gates A and B on `child = 0x086e2780`, duration `1200.0f`) were captured in Azahar (`h1-track-runtime`), the full `#if 0` callback draft readiness was audited (`h1-main-callback-editable-readiness`), and the production State-5 readiness/navigation/event-request slice (`H1_TitleMain_UpdateNavigationSlice` at `0x001E9D08..0x001E9DDC` inside `ui_func_001e989c`) was integrated and verified across a 258-case full-callback differential matrix, a 4-selection transition/fade/help-lookup composition, and an 11-step original-versus-patched Azahar runtime comparison (`h1-menu-slice-integration`). All 80 planned tasks on the current H1 board (`config/agent-workflows/h1.json`) are accepted; remaining callback states (`0–4`, `6–12`) and downstream State-5 slices are documented in the H1 milestone record.

## Separate evidence dimensions

| Dimension | Meaning | Source |
| --- | --- | --- |
| Exact bytes | Original machine code reproduced, including assembly/raw wrappers | `PROGRESS.md` and the exact audit |
| Experimental C++ presence | Candidate definitions exist; includes partial and exact-code experiments | [Generated inventory](semantic-inventory.md) |
| Differential evidence | Original and compiled C++ agree within the tested contract and cases | Per-address experiment reports and fresh test outputs |
| Integrated replacement | The selected compiled C++ is installed and reached through real callers | Patch hashes, caller checks, and integration records |
| Runtime scenario | The defined original-versus-patched scenario meets acceptance criteria | H0/H1 milestone records |

Do not add these dimensions into a completion percentage. Historical aggregate counts have different scopes; the generated inventory replaces manually copied presence counts, not per-function equivalence decisions. Prefix experiments and projected-output results must remain explicitly partial. In particular, the TexConv sliding-average report leaves calling-convention equivalence unresolved.

## Agentic execution

Follow the [coordinator/subagent workflow](agent-workflow.md). The tracked H1 board
assigns bounded contracts, implementation, independent review and integration,
with exclusive file/runtime ownership, private outputs and an eight-job CPU budget.
`python tools/agent_workflow.py ready` lists tasks whose prerequisites are accepted.
Only the coordinator claims tasks and changes board state.

## Efficient development loop

1. Pick the smallest coherent batch that advances H1. Recover types and call contracts with it.
2. Run focused differential/caller tests during development, including boundary cases and negative controls. Reuse shared runner infrastructure.
3. Close a batch with the relevant wider regression and affected build checks. Audit exact-reference claims when those claims/tools change; a byte mismatch alone does not reject semantic C++. Save artifacts under ignored `build/`.
4. Promote accepted candidates through a reproducible experimental patch. Compare the same scenario against the original and document remaining original dependencies.
5. Keep the exact baseline available as a reference. A complete standalone link is a later milestone; controlled replacements can deliver editable systems sooner.

Refresh static inventory with:

```powershell
python tools/audit_semantic_candidates.py --output build/semantic-equivalence/semantic-candidate-audit.json --markdown-output docs/semantic-inventory.md
```

Inventory links do not certify test execution. Test totals belong to a dated validation record, rather than a manually maintained README claim.
