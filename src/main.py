from __future__ import annotations

import argparse
import json
from pathlib import Path

from .public_api import API_VERSION, compile_paper, validate_markdown, verify_compilation
from .question_formatter import format_document
from .render_validator import validate_rendered_markdown


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="TheMITbro mathematical Markdown formatter / M25 public compiler"
    )
    parser.add_argument(
        "input",
        type=Path,
        nargs="?",
        help="Markdown input file (legacy formatter mode).",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Markdown output file (legacy formatter mode).",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate the rendered Markdown in legacy formatter mode.",
    )
    parser.add_argument(
        "--compile-json",
        type=Path,
        metavar="PAPER_JSON",
        help="Compile a structured PaperSpec JSON document end-to-end.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory for --compile-json.",
    )
    parser.add_argument(
        "--formats",
        default="markdown,svg,pdf,html",
        help="Comma-separated formats for --compile-json.",
    )
    parser.add_argument(
        "--verify-output",
        type=Path,
        metavar="OUTPUT_DIR",
        help="Verify an existing M26 compilation bundle.",
    )
    parser.add_argument(
        "--expected-input-sha256",
        help="Optional input SHA-256 expected by --verify-output.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"TheMITbro Formatter API {API_VERSION} / M25 + M26 build contract",
    )
    return parser


def _run_legacy(args: argparse.Namespace) -> int:
    if args.input is None or args.output is None:
        raise SystemExit(
            "Legacy mode requires both INPUT and --output. "
            "Use --compile-json for end-to-end paper compilation."
        )

    source = args.input.read_text(encoding="utf-8")
    formatted = format_document(source)

    if args.validate:
        checks = validate_rendered_markdown(source)
        for check in checks:
            print(("PASS" if check.passed else "FAIL") + ": " + check.name)
        if not all(check.passed for check in checks):
            return 2

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(formatted, encoding="utf-8")
    print(f"Formatted: {args.input} -> {args.output}")
    return 0


def _run_compile(args: argparse.Namespace) -> int:
    if args.output_dir is None:
        raise SystemExit("--compile-json requires --output-dir.")

    paper = json.loads(args.compile_json.read_text(encoding="utf-8"))
    formats = tuple(
        item.strip().lower()
        for item in args.formats.split(",")
        if item.strip()
    )
    result = compile_paper(paper, args.output_dir, formats=formats)

    print(f"Status: {result.status}")
    print(f"API contract: {result.api_contract}")
    print(f"Compiler: {result.compiler_version}")
    print(f"Questions: {result.question_count}")
    print(f"Pages: {result.page_count}")
    print(f"Artifacts: {len(result.artifacts)}")
    for artifact in result.artifacts:
        print(
            f"  {artifact.kind}: {artifact.path} "
            f"({artifact.bytes} bytes, {artifact.sha256})"
        )
    return 0

def _run_verify(args: argparse.Namespace) -> int:
    if args.verify_output is None:
        raise SystemExit("--verify-output requires an output directory.")
    report = verify_compilation(
        str(args.verify_output),
        expected_input_sha256=args.expected_input_sha256,
    )
    print("Status: VERIFIED")
    print(f"Build contract: {report['build_contract']}")
    print(f"Input SHA-256: {report['input_sha256']}")
    print(f"Artifacts verified: {report['artifact_count']}")
    return 0



def main() -> int:
    args = build_parser().parse_args()

    verify_output = getattr(args, "verify_output", None)

    if verify_output is not None:
        if (
            args.input is not None
            or args.output is not None
            or args.compile_json is not None
        ):
            raise SystemExit(
                "--verify-output cannot be combined with formatter/compiler inputs."
            )
        return _run_verify(args)

    if args.compile_json is not None:
        if args.input is not None or args.output is not None:
            raise SystemExit(
                "--compile-json cannot be combined with legacy INPUT/--output."
            )
        return _run_compile(args)

    return _run_legacy(args)


if __name__ == "__main__":
    raise SystemExit(main())
