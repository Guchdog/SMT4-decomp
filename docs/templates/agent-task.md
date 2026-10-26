# Agent task contract

The coordinator fills the tracked board and generates a fresh brief with
`tools/agent_workflow.py prepare`. This is a checklist, not a second competing
function-evidence record.

- **Milestone and bounded outcome:** observable behavior/dependency unlocked.
- **Role and owner:** recon, implementation, validation or integration; one agent.
- **Addresses:** callable entry versus interior range, with original reference.
- **Starting state:** branch/HEAD plus actual dirty input hashes from the packet.
- **Exclusive edits:** exact candidate, test and record paths; shared files excluded.
- **Frozen inputs:** callers, headers, runner interfaces, existing attempts/results.
- **Dependencies:** accepted contracts required before starting, not merely a reply.
- **Runner and checks:** existing supported runner or an explicit support prerequisite;
  exact commands/CLI output shape, boundaries/branches/aliasing, two seeds where
  appropriate, negative controls and real caller observations.
- **Resource allocation:** compiler jobs, private output root, any exclusive runtime
  resource; no implicit use of canonical cache or global full regression.
- **Acceptance and limitations:** supported evidence level, missing fixtures,
  unsupported semantics and scope that must remain original.
- **Handoff:** changed-file/report hashes, command exits, evidence and next action
  in `agent-handoff.json`, pointing to per-function records rather than copying them.

Independent review must challenge the contract and controls before promotion.
If the task cannot meet its contract, return a bounded blocker and unblock condition;
do not silently broaden scope or require byte-identical C++.
