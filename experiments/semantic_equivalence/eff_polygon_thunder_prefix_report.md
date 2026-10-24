# EffPolygonThunder point-count prefix experiment

## Scope

This is a bounded differential check of the point-count normalization prefix,
not a reconstruction or validation of the three complete geometry constructors.
It uses the pinned US `code.bin` and stops the original ARM execution before
geometry allocation/rendering. Candidate functions only implement the observed
normalization of `object+0x3C`.

## Observed behavior

- `0x0031596C`, prefix `0x003159DC`–`0x003159F4`: clamps unsigned `points` to
  at least 3.
- `0x0032170C`, prefix `0x00321764`–`0x0032177C`: same minimum clamp.
- `0x00327D90`, prefix `0x00327DEC`–`0x00327E18`: same clamp, then increments
  an even result to make it odd.

The prefix reads the object pointer from the caller's stack slot and writes only
the four-byte `object+0x3C` field. This test compares that final field and the
observable write footprint. It does not compare the preceding allocator/factory
work, later vertex generation, return value, full register state, or caller
behavior.

## Differential evidence

Run:

```powershell
python -m unittest tests.test_eff_polygon_thunder_prefix_experiment -v
```

The test passed for all three prefixes. With seed `20261024`, each prefix was
compared over 646 counts: every value from 0 through 511, six high-boundary
values (`0x7FFFFFFF`, `0x80000000`, and `0xFFFFFFFC` through `0xFFFFFFFF`), and
128 deterministic random values. All three negative controls were detected:
minimum 2 instead of 3 on each non-oddifying prefix, and omission of oddifying
on the third. The test compiles the candidate helpers for ARMv6K and executes
both the original prefix and candidate in Unicorn against ordinary mapped RAM.

## Limits

This establishes parity only for the normalized count and its write footprint
over the tested domain. It does not establish equivalence of any full
`EffPolygonThunder` constructor, production integration, actual caller setup,
allocation behavior, geometry/render output, or hardware/OS memory-fault
behavior. Keep this micro-result separate from a count of fully reconstructed
functions.
