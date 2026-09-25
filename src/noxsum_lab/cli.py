from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

from .generator import generate_levels
from .import_grant import import_grant_pack
from .solver import validate_campaign


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


def cmd_revalidate_grant(args: argparse.Namespace) -> int:
    source = _read_json(Path(args.input))
    if not isinstance(source, list):
        raise ValueError("Grant campaign must be a JSON array.")

    results = validate_campaign(source)
    for result in results:
        solution = result.solutions[0]
        object_text = ",".join(
            f"{item['cell']}:{item['type']}"
            for item in solution.as_dict()["objects"]
        )
        shutter = "-" if solution.shutter is None else str(solution.shutter)
        print(
            f"{result.stage_id}: states={result.searched_states}, unique=1, "
            f"objects={object_text}, lights={'+'.join(solution.lights)}, "
            f"shutter={shutter}"
        )

    print(
        f"PASS: {len(results)} stages, "
        f"{sum(result.searched_states for result in results)} states searched"
    )
    return 0


def _parse_lights(value: str) -> tuple[str, ...]:
    lights = tuple(
        item.strip().upper()
        for item in value.split(",")
        if item.strip()
    )
    if not lights:
        raise argparse.ArgumentTypeError("at least one light is required")
    allowed = {"TOP", "LEFT", "RIGHT", "BOTTOM"}
    unknown = set(lights) - allowed
    if unknown:
        raise argparse.ArgumentTypeError(
            "unknown lights: " + ", ".join(sorted(unknown))
        )
    return lights


def _parse_mask(value: str) -> list[str]:
    rows = [item.strip() for item in value.split("/")]
    if len(rows) != 5 or any(len(row) != 5 or set(row) - {"0", "1"} for row in rows):
        raise argparse.ArgumentTypeError(
            "mask must be five 5-character 0/1 rows separated by /"
        )
    return rows


def cmd_generate(args: argparse.Namespace) -> int:
    levels = generate_levels(
        seed=args.seed,
        count=args.count,
        normal=args.normal,
        tall=args.tall,
        plate=args.plate,
        lights=args.lights,
        board_mask=args.mask,
    )
    _write_json(Path(args.output), levels)
    print(
        f"Generated {len(levels)} exact-unique candidates -> {args.output} "
        f"(seed={args.seed})"
    )
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

    revalidate = sub.add_parser(
        "revalidate-grant",
        help="Exhaustively revalidate a NOXSUM Grant campaign",
    )
    revalidate.add_argument(
        "input",
        nargs="?",
        default="fixtures/grant36_v0_5.json",
    )
    revalidate.set_defaults(func=cmd_revalidate_grant)

    generate = sub.add_parser(
        "generate",
        help="Generate deterministic exact-unique candidates",
    )
    generate.add_argument("output")
    generate.add_argument("--seed", type=int, default=20260925)
    generate.add_argument("--count", type=int, default=20)
    generate.add_argument("--normal", type=int, default=3)
    generate.add_argument("--tall", type=int, default=0)
    generate.add_argument("--plate", type=int, default=0)
    generate.add_argument(
        "--lights",
        type=_parse_lights,
        default=("TOP", "LEFT", "RIGHT"),
        help="comma-separated fixed lights",
    )
    generate.add_argument(
        "--mask",
        type=_parse_mask,
        default=None,
        help="five board-mask rows separated by /",
    )
    generate.set_defaults(func=cmd_generate)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
