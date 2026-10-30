#!/usr/bin/env python3
"""Inventory semantic C++ candidates and link observable test/report evidence.

This is an audit, not an approval tool: source presence, a linked differential
test, and a linked Markdown report are reported as separate facts.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


_CANDIDATE = re.compile(r"\bcandidate_[A-Za-z0-9_]+\b")
_HEX_ADDRESS = re.compile(r"candidate_([0-9a-fA-F]{8})(?![0-9a-fA-F])")
_ADDRESS = re.compile(r"(?<![0-9a-fA-F])(?:0x)?([0-9a-fA-F]{8})(?![0-9a-fA-F])", re.I)


def _strip_cpp_noncode(text: str) -> str:
    """Blank comments and literals while preserving offsets and newlines."""
    out = list(text)
    i, n = 0, len(text)
    while i < n:
        if text.startswith("//", i):
            end = text.find("\n", i)
            end = n if end < 0 else end
            for j in range(i, end):
                out[j] = " "
            i = end
        elif text.startswith("/*", i):
            end = text.find("*/", i + 2)
            end = n if end < 0 else end + 2
            for j in range(i, end):
                if text[j] != "\n":
                    out[j] = " "
            i = end
        elif text[i] in ('"', "'"):
            quote = text[i]
            j = i + 1
            while j < n:
                if text[j] == "\\":
                    j += 2
                elif text[j] == quote:
                    j += 1
                    break
                else:
                    j += 1
            for k in range(i, min(j, n)):
                if text[k] != "\n":
                    out[k] = " "
            i = j
        else:
            i += 1
    return "".join(out)


def _candidate_definitions(path: Path) -> set[str]:
    code = _strip_cpp_noncode(path.read_text(encoding="utf-8", errors="replace"))
    # Join preprocessor continuations, retaining line separation for other code.
    logical = re.sub(r"\\\r?\n[ \t]*", " ", code)
    definitions: set[str] = set()

    # Ordinary out-of-line function definitions: a candidate declarator whose
    # balanced parameter list is followed by a body. References/calls do not fit.
    for match in _CANDIDATE.finditer(logical):
        symbol = match.group(0)
        if symbol.startswith("negative_candidate_"):
            continue
        pos = match.end()
        while pos < len(logical) and logical[pos].isspace():
            pos += 1
        if pos >= len(logical) or logical[pos] != "(":
            continue
        depth, i = 1, pos + 1
        while i < len(logical) and depth:
            depth += (logical[i] == "(") - (logical[i] == ")")
            i += 1
        if depth:
            continue
        while i < len(logical) and logical[i].isspace():
            i += 1
        if i < len(logical) and logical[i] == "{":
            definitions.add(symbol)

    # Function-generating macros. A candidate argument is accepted only when
    # a parameter used as a function declarator in the macro replacement body
    # actually expands to a definition (the replacement contains that body).
    macros: dict[str, tuple[str, str]] = {}
    for m in re.finditer(
        r"(?m)^\s*#\s*define\s+(\w+)\s*\(([^)]*)\)([^\n]*)", logical
    ):
        params = [x.strip() for x in m.group(2).split(",") if x.strip()]
        body = m.group(3)
        if "{" not in body:
            continue
        for param in params:
            if re.search(rf"\b{re.escape(param)}\s*\(", body):
                macros[m.group(1)] = (params.index(param), body)
                break
    for macro, (function_arg_index, _body) in macros.items():
        for call in re.finditer(rf"\b{re.escape(macro)}\s*\(([^\n]*)\)", logical):
            args = [x.strip() for x in call.group(1).split(",")]
            if (function_arg_index < len(args)
                    and _CANDIDATE.fullmatch(args[function_arg_index])):
                definitions.add(args[function_arg_index])
    return definitions


def audit(root: Path) -> dict:
    exp = root / "experiments" / "semantic_equivalence"
    sources = sorted(exp.glob("*.cpp"))
    by_symbol: dict[str, list[str]] = {}
    for source in sources:
        for symbol in _candidate_definitions(source):
            by_symbol.setdefault(symbol, []).append(source.relative_to(root).as_posix())

    tools = {p.stem: p.read_text(encoding="utf-8", errors="replace")
             for p in (root / "tools").glob("*.py")}
    tests = {p.stem: p.read_text(encoding="utf-8", errors="replace")
             for p in (root / "tests").glob("test_*.py")}
    reports = {p.relative_to(root).as_posix(): p.read_text(encoding="utf-8", errors="replace")
               for p in exp.glob("*.md")}
    candidates = []
    for symbol, source_paths in sorted(by_symbol.items()):
        addresses = {m.group(1).lower() for m in _HEX_ADDRESS.finditer(symbol)}
        linked_tools = []
        for name, text in tools.items():
            direct_symbol_link = symbol in text
            source_link = False
            for source_path in source_paths:
                source_file = Path(source_path).name
                quoted_source = re.search(
                    rf"['\"][^'\"]*{re.escape(source_file)}[^'\"]*['\"]", text
                )
                address_link = any(
                    re.search(rf"(?<![0-9a-fA-F])0x{address}(?![0-9a-fA-F])", text, re.I)
                    for address in addresses
                )
                if quoted_source and (address_link or not addresses):
                    source_link = True
                    break
            if direct_symbol_link or source_link:
                linked_tools.append(name)
        linked_tests = [test_name for test_name, text in tests.items()
                        if any(re.search(
                            rf"(?:from\s+tools\.{re.escape(name)}\s+import\b|"
                            rf"import\s+tools\.{re.escape(name)}\b)", text)
                            for name in linked_tools)]
        # A linked test is marked differential only when it both links to the
        # importing test module and asserts a passing experiment result/cases.
        differential_test_checks = []
        for test_name in linked_tests:
            body = tests[test_name]
            test_modules = [name for name in linked_tools
                            if re.search(rf"\b{re.escape(name)}\b", body)]
            linked_runner = any(
                re.search(r"\b(function_comparisons|difference|validate_leaf)\s*\b",
                          tools[name])
                for name in test_modules
            )
            checks_pass = bool(re.search(
                r"assert(?:True|Equal)\([^\n]*(?:passed|function_comparisons|cases)",
                body, re.I))
            if linked_runner and checks_pass:
                differential_test_checks.append(test_name)
        linked_reports = []
        for report_path, body in reports.items():
            report_addresses = {x.lower() for x in _ADDRESS.findall(body)}
            if symbol in body or (addresses and addresses & report_addresses):
                linked_reports.append(report_path)
        candidates.append({
            "symbol": symbol,
            "kind": ("address_named_candidate" if re.fullmatch(
                r"candidate_[0-9a-fA-F]{8}", symbol) else "prefix_or_helper"),
            "source_files": source_paths,
            "presence": True,
            "linked_tool_modules": linked_tools,
            "linked_tests": linked_tests,
            "differential_test_checks": differential_test_checks,
            "associated_reports": linked_reports,
        })
    return {
        "schema_version": 2,
        "root": str(root),
        "source_file_count": len(sources),
        "candidate_count": len(candidates),
        "counts": {
            "source_presence": len(candidates),
            "address_named_candidates": sum(
                x["kind"] == "address_named_candidate" for x in candidates),
            "prefix_or_helper_candidates": sum(
                x["kind"] == "prefix_or_helper" for x in candidates),
            "with_linked_test": sum(bool(x["linked_tests"]) for x in candidates),
            "with_differential_test_check": sum(bool(x["differential_test_checks"]) for x in candidates),
            "with_associated_report": sum(bool(x["associated_reports"]) for x in candidates),
        },
        "evidence_note": "Links are static associations only; this inventory does not certify test execution, equivalence, or approval.",
        "candidates": candidates,
    }


def render_markdown(result: dict) -> str:
    """Render measured inventory facts without promoting static links to passes."""
    counts = result["counts"]
    lines = [
        "# Semantic candidate inventory", "",
        "Generated by `python tools/audit_semantic_candidates.py "
        "--output build/semantic-equivalence/semantic-candidate-audit.json "
        "--markdown-output docs/semantic-inventory.md`.", "",
        "These counts describe experimental source definitions and static evidence links. "
        "They do not count equivalent, integrated, or runtime-validated functions.", "",
        "| Inventory dimension | Count |", "| --- | ---: |",
        f"| Candidate translation units | {result['source_file_count']} |",
        f"| Address-named candidate definitions | {counts['address_named_candidates']} |",
        f"| Prefix/control/helper candidate definitions | {counts['prefix_or_helper_candidates']} |",
        f"| Total candidate definitions | {result['candidate_count']} |",
        f"| Definitions linked to test modules | {counts['with_linked_test']} |",
        f"| Definitions linked to differential-shaped assertions | {counts['with_differential_test_check']} |",
        f"| Definitions associated with Markdown reports | {counts['with_associated_report']} |",
        "", "## How to interpret progress", "",
        "- Source inventory: the measured definitions below, including partial and exact-code experiments.",
        "- Differential evidence: bounded original-versus-C++ executions recorded by each experiment; "
        "a static test link does not establish that the experiment ran or passed.",
        "- Integrated replacement: code installed in a reproducible patch and reached by its real callers.",
        "- Runtime validation: the documented scenario and observed behavior, with remaining original dependencies.",
        "", "Historical totals such as 169 semantic candidates and 229 combined functions used "
        "different scopes. Do not add this inventory to the byte-exact milestone or interpret a "
        "coincidentally equal number as reconciliation. Promotion requires per-address evidence "
        "and the [functional acceptance criteria](reconstruction-milestones.md).", "",
        "## Definitions", "",
        "| Symbol | Kind | Source | Test links | Differential check links | Report links |",
        "| --- | --- | --- | ---: | ---: | ---: |",
    ]
    for item in result["candidates"]:
        sources = ", ".join(f"[{Path(path).name}](../{path})" for path in item["source_files"])
        lines.append(f"| `{item['symbol']}` | {item['kind']} | {sources} | "
                     f"{len(item['linked_tests'])} | {len(item['differential_test_checks'])} | "
                     f"{len(item['associated_reports'])} |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--output", type=Path, help="write JSON here; default prints to stdout")
    parser.add_argument("--markdown-output", type=Path, help="write a generated inventory report here")
    args = parser.parse_args()
    result = audit(args.root.resolve())
    if args.markdown_output:
        args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
        args.markdown_output.write_text(render_markdown(result), encoding="utf-8")
    rendered = json.dumps(result, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
