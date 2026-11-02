# H2 `0x00296F18` cursor-axis conversion

The naked ARM body was replaced with typed C++ in `src/engine/leaf_batch11_b.cpp`. The candidate retains the three-argument ABI, signed `start <= 0` clamp, ten-word initialization, ordered volatile stores, and raw `r0` result observed from the pinned original. It compiles to 68 bytes in the original 72-byte slot with no relocations.

Run the offline differential and caller composition with a fresh output directory:

```powershell
python tools/h2_296f18_cursor_axis_experiment.py --out build/agent-work/H2-semantic/h2-cursor-axis-setup-00296f18-convert/run001/checks/<run-name> --seed 20261130
```

The reviewed run002 report and one-slot IPS are under `build/agent-work/H2-semantic/h2-cursor-axis-setup-00296f18-convert/run002/checks/coordinator-seed-20261130/` (report SHA-256 `2084459247d927b20f8b9b43c93f68c2568ccb5ed15ee05ea7eb897d0458b681`). It passed 61 direct cases, a mapped-boundary fault comparison, three detected negative controls, exact ARM interworking checks, and the actual `0x0029FAE8` caller. The caller assertions require both dynamic helper arguments and both ten-word final axis records; the wrapper finalizes both starts to 1 after the helper's intermediate constant 2.

Independent review found no counterexample in the aligned ordinary-RAM domain and confirmed the caller assertions. See [review run001](h2-296f18-independent-review.md) and [review run002](h2-296f18-independent-review-run002.md). The one-slot differential retains every sibling helper from the original. Runtime, lifecycle, input mapping, and whole-title equivalence remain unverified.
