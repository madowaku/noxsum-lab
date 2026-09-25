from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .import_grant import import_grant_pack


DEFAULT_SCHEMA = Path("schemas/noxsum_level_v1.schema.json")


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _load_validator(schema_path: Path) -> Draft202012Validator:
    schema = _read_json(schema_path)
    return Draft202012Validator(schema)


def _iter_levels(data: Any) -> list[dict[str, Any]]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        return [data]
    raise ValueError("Level JSON must be an object or an array of objects.")


def cmd_validate(args: argparse.Namespace) -> int:
    data = _read_json(Path(args.input))
    validator = _load_validator(Path(args.schema))

    failed = False
    for index, level in enumerate(_iter_levels(data)):
        errors = sorted(validator.iter_errors(level), key=lambda e: list(e.path))
        if not errors:
            print(f"OK  [{index}] {level.get('id', '<no id>')}")
            continue

        failed = True
        print(f"NG  [{index}] {level.get('id', '<no id>')}")
        for error in errors:
            where = ".".join(str(part) for part in error.path) or "<root>"
            print(f"    {where}: {error.message}")

    return 1 if failed else 0


def cmd_import_grant(args: argparse.Namespace) -> int:
    source = _read_json(Path(args.input))
    if not isinstance(source, list):
        raise ValueError("Grant pack must be a JSON array.")

    canonical = import_grant_pack(
        source,
        repo=args.repo,
        ref=args.ref,
        path=args.source_path or args.input,
    )
    _write_json(Path(args.output), canonical)
    print(f"Imported {len(canonical)} levels -> {args.output}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="noxsum-lab")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="Validate canonical level JSON")
    validate.add_argument("input")
    validate.add_argument("--schema", default=str(DEFAULT_SCHEMA))
    validate.set_defaults(func=cmd_validate)

    imp = sub.add_parser("import-grant", help="Import current Grant JSON")
    imp.add_argument("input")
    imp.add_argument("output")
    imp.add_argument("--repo", default="madowaku/shadow-sum")
    imp.add_argument("--ref", default=None)
    imp.add_argument("--source-path", default=None)
    imp.set_defaults(func=cmd_import_grant)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
