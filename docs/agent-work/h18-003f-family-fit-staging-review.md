# Independent review: 003f initializer private staging

Owner: `luna_probe_review`; task: `h18-003f-family-fit-staging-review`.

## Result

I reran the staging utility with fresh seed `20261119` and 20 samples. It passed with 11 placements, staged image SHA-256 `e886bd9e322129e93cf7b8cbad7e3cfe705fc55981b1e37de8f93cbb95a36e53`, and IPS SHA-256 `d94d484cbb1e087e74e07eb845b772e5f98730ac568a34c2254b963fa7dc519c`. The 11 slots are the expected `0x003f3274`, eight entries `0x003f32f4..0x003f3428`, and `0x003f34a0`/`0x003f34cc`; each candidate is word aligned and fits its assigned exact interval.

The fresh functional report has 20 passing cases for each of the 11 staged candidates (220 total), and 20 passing original-vs-staged executions of the preserved `0x003f3454` entry. The 15 negative controls were all detected (5 for `0x3274`, 8 for the `0x32f4` family, and 2 for the `0x34a0/34cc` pair). The preserved `0x3454` execution observed the ARM-to-Thumb transition in all 20 cases.

## Independent byte/IPS audit

A separate audit of the fresh staged image and IPS decoded the emitted IPS records. It confirmed:

- Pinned original image hash and staged/IPS hashes match the report.
- IPS replay reproduces the staged image; exactly 11 IPS data records match the 11 candidate body starts and lengths.
- All 11 candidate bodies fit their exact slots and have aligned ARM entry VMAs.
- The 361 changed bytes are confined to the emitted candidate body ranges.
- Existing `[0x003f31d8,0x003f3274)` is unchanged; excluded oversized `[0x003f3454,0x003f34a0)` is byte-identical; bytes outside compound `[0x003f31d8,0x003f34f8)` are unchanged.

The existing unit suite passed both tests: `test_exact_eleven_slots_stage_and_roundtrip_without_3454` and `test_oversized_or_extra_entry_is_rejected`.

## Evidence limits

The staged entries were compiled and differentially executed offline in Unicorn at their final VMAs against the pinned original under synthetic fixtures. The preserved `0x3454` path uses the existing modeled iterator/constructor behavior. No actual startup caller or initialization order is established; the report correctly says caller `not_run`. No emulator or runtime/game scenario was run. This does not establish production integration or whole-game equivalence.

## Recommendation

The private staging, exact slot bounds, image preservation, IPS replay, final-VMA functional cases, and controls are supported by this fresh evidence. Keep the result as a private experimental artifact. Caller/startup integration and real iterator behavior remain prerequisites for promotion.
