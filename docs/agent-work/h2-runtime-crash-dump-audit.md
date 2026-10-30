# H2 patched runtime crash dump offline audit

## Findings

The preserved 207,147,138-byte minidump hashes to `d6508058309f09c067795698f883a1ab07f80cd7ad257354e7e8f6d367238712`. Its exception stream records thread ID 5360, code `0x20474343`, flags 0, and instruction address `KERNELBASE.dll+0x25369`; the saved Windows Application Error event reports the same code and module offset for PID 19040 and the staged patched executable. The dump lists 134 modules, including that staged Azahar executable, KERNELBASE, ntdll, libc++ and libunwind. This is a host exception site, not a guest ARM instruction.

The exception code is consistent with `STATUS_GCC_THROW` used by LLVM libunwind's SEH implementation for `_Unwind_RaiseException` ([libunwind source](https://llvm.googlesource.com/libunwind/+/9defb52f575beff21b646e60e63f72ad1ac7cf54/src/Unwind-seh.cpp)). This is an interpretation of the numeric code, not proof of the thrown type, its origin or why it was unhandled. The event records a terminated application; the report records the user's observation that the window closed while opening Audio Settings. The saved log independently shows the staged H2 IPS patching `code.bin` and the intended title ID, but does not identify which replacement ran or the throw source. Its last line is truncated.

The exception thread's saved x64 context places RIP at the above KERNELBASE address; a 6,688-byte thread stack is captured. A scan of its first 1,024 bytes finds values in Azahar, libunwind and libc++ module ranges, including Azahar-relative `0x17be8c8`, `0x1707f`, `0x1461084`, and libc++-relative `0xaec92`/`0xaedca`. These are **candidate stack values, not unwound frames or proven return addresses**. No trustworthy stack trace or throwing call site was established without correct unwind/symbol information. The sole exception parameter points outside every captured memory range, so this dump does not expose the exception object at that address. No guest PC, guest register state, exception type/message, or specific patched function was identified. The dump's limited captured memory cannot prove that such evidence was absent from the live process.

## Next action

Keep the original dump private and preserve its hash. Use a suitable offline minidump debugger plus matching executable, DLL unwind metadata and symbols to obtain a validated stack and thrown type if possible; do not treat raw stack values as frames. If that remains insufficient, design a separately reviewed, bounded reproduction/instrumentation plan to identify guest PC and host throw while maintaining the existing runtime safety constraints. No H2 behavioral equivalence or specific causation follows from the crash alone.

This audit read the preserved dump, event and log offline. It did not launch, attach to, or control a target, use sockets or input, or change firewall settings. Raw memory is not included in this note.
