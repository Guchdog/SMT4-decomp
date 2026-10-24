# TexConv sliding-average helper: projected differential result

Status: output/memory parity passes for the tested scenarios; full semantic
equivalence is **not established** because the original and C++ helper differ
in preserved-register state and no caller window/calling-convention evidence is
available.

## What was checked

The three pinned ARM functions are `0x001721E4`, `0x001787E4`, and
`0x0017EDE4`, each 136 bytes. Their normalized 34-instruction bodies match;
the per-copy tile strides are `0x400`, `0x100`, and `0x200`. The reference
`code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

`TexConv_001721e4` in `src/engine/tex_convert.cpp` is a
`[[maybe_unused]] static` definition, and the source-wide scan found only that
definition (no production caller). It is therefore a dormant C++ draft, not an
active replacement. The experiment includes that source unchanged in an
isolated adapter TU and calls the existing helper with each clone's stride;
production files and the matching ledger were not edited.

## Results

For each of two seeds (`7`, `20261024`), each clone matched its original on 13
bounded executions: count 1/2/3/5 boundary-pattern cases, an all-zero case,
and eight seeded random cases with counts 1 through 8. That is **78 projected
function comparisons total**. Output data, observable read/write footprint,
return flow, stack-visible state, and the other preserved registers matched.
Both negative controls were detected for each seed (**4/4**): using stride
`0x400` against the `0x100` clone, and copying a row instead of performing the
sliding average. Count zero is rejected before emulation because the original
is a do-while loop; no invalid pointer or out-of-bounds case is run.

The ABI difference is concrete and repeated for all three originals:

- ARM originals overwrite `r7` and `r9`/`SB` without restoring them.
- The compiled C++ adapters preserve all callee-saved registers, including
  `r7` and `r9`, as required by the standard AAPCS contract.

Those differences are deliberately not folded into a general “pass.” They can
be visible to a caller if the game uses a convention that relies on these
registers being clobbered. No verified direct caller or indirect-dispatch
window was tested, so this experiment establishes only *projected pixel-buffer
transformation parity*, not drop-in equivalence or production safety.

## Reproduction

```powershell
python -m unittest tests.test_texconv_sliding_average_experiment -v
python tools/texconv_sliding_average_experiment.py --samples 8 --seed 7 --output build/semantic-equivalence/texconv-sliding-average-seed-7
python tools/texconv_sliding_average_experiment.py --samples 8 --seed 20261024 --output build/semantic-equivalence/texconv-sliding-average-seed-20261024
```

The runner links the isolated C++ object at a fixed test address so calls to
the private existing helper and its freestanding `memcpy` can execute in the
same Unicorn ARMv6K machine as the pinned original image. This does not patch
or rebuild the game image.
