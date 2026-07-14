from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


def default_output_path(input_path: Path) -> Path:
    output_name = input_path.with_suffix(".json").name
    if input_path.parent.name == "input":
        return input_path.parent.parent / "output" / output_name
    return input_path.parent / "output" / output_name


def default_bad_output_path(output_path: Path) -> Path:
    return output_path.parent / "bad" / f"{output_path.stem}.bad.json"


def parse_args(description: str) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--input", required=True, type=Path, help="Oracle JSON_OBJECT export file to repair")
    parser.add_argument(
        "--output",
        type=Path,
        help="repaired JSON Lines output file. Default: output/<input file name>.json",
    )
    parser.add_argument(
        "--bad-output",
        type=Path,
        help="bad rows output file. Default: output/bad/<input stem>.bad.json",
    )
    parser.add_argument("--encoding", default="utf-8", help="input/output encoding")
    parser.add_argument("--progress-interval", type=int, default=100_000, help="progress print interval")
    parser.add_argument("--limit", type=int, default=0, help="stop after N input rows for test runs")
    parser.add_argument(
        "--keep-empty-string",
        action="store_true",
        help="keep empty values as empty string instead of null",
    )
    args = parser.parse_args()

    if args.output is None:
        args.output = default_output_path(args.input)
    if args.bad_output is None:
        args.bad_output = default_bad_output_path(args.output)

    return args


def strip_outer_object(line: str) -> str:
    value = line.strip().lstrip("\ufeff")
    if value.startswith("{"):
        value = value[1:]
    if value.endswith("}"):
        value = value[:-1]
    return value


def find_first_key_value_start(body: str, first_column: str) -> int:
    match = re.search(rf'"{re.escape(first_column)}"\s*:', body)
    if not match:
        raise ValueError(f"missing key: {first_column}")
    return match.end()


def find_next_key(body: str, next_column: str, value_start: int) -> re.Match[str]:
    pattern = rf',\s*"{re.escape(next_column)}"\s*:'
    match = re.search(pattern, body[value_start:])
    if not match:
        raise ValueError(f"missing next key delimiter: {next_column}")
    return match


def extract_values_by_columns(line: str, columns: list[str]) -> dict[str, str]:
    body = strip_outer_object(line)
    values: dict[str, str] = {}
    value_start = find_first_key_value_start(body, columns[0])

    for index, column in enumerate(columns):
        if index + 1 < len(columns):
            next_column = columns[index + 1]
            match = find_next_key(body, next_column, value_start)
            raw = body[value_start : value_start + match.start()].strip()
            value_start = value_start + match.end()
        else:
            raw = body[value_start:].strip()

        values[column] = raw

    return values


def decode_escaped_fragments(value: str) -> str:
    # Try valid JSON string decoding first. If source is malformed, recover the
    # common escape sequences and let json.dumps produce valid JSON output later.
    value = value.replace(r"\"", '"')
    value = value.replace(r"\n", "\n")
    value = value.replace(r"\r", "\r")
    value = value.replace(r"\t", "\t")
    value = value.replace(r"\\", "\\")
    return value


def parse_string_value(raw: str, keep_empty_string: bool) -> str | None:
    value = raw.strip()

    if value.lower() == "null":
        return None
    if value == "" and not keep_empty_string:
        return None

    if value.startswith('"') and value.endswith('"'):
        try:
            decoded = json.loads(value)
            if decoded == "" and not keep_empty_string:
                return None
            return decoded
        except json.JSONDecodeError:
            value = value[1:-1]

    value = decode_escaped_fragments(value)
    if value == "" and not keep_empty_string:
        return None
    return value


def parse_number_value(raw: str) -> int | float | None:
    value = raw.strip()
    if value.lower() == "null" or value == "":
        return None

    if value.startswith('"') and value.endswith('"'):
        value = parse_string_value(value, keep_empty_string=True) or ""

    if re.fullmatch(r"[-+]?\d+", value):
        return int(value)
    return float(value)


def repair_line(
    line: str,
    columns: list[str],
    string_fields: set[str],
    number_fields: set[str],
    keep_empty_string: bool,
) -> dict[str, Any]:
    raw_values = extract_values_by_columns(line, columns)
    repaired: dict[str, Any] = {}

    for column in columns:
        raw = raw_values[column]
        if column in number_fields:
            repaired[column] = parse_number_value(raw)
        elif column in string_fields:
            repaired[column] = parse_string_value(raw, keep_empty_string=keep_empty_string)
        else:
            repaired[column] = parse_string_value(raw, keep_empty_string=keep_empty_string)

    return repaired


def repair_file(
    *,
    input_path: Path,
    output_path: Path,
    bad_output_path: Path,
    encoding: str,
    columns: list[str],
    string_fields: set[str],
    number_fields: set[str],
    keep_empty_string: bool,
    progress_interval: int,
    limit: int,
    table_name: str,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    bad_output_path.parent.mkdir(parents=True, exist_ok=True)

    rows = 0
    bad_rows = 0
    input_rows = 0

    with (
        input_path.open("r", encoding=encoding, errors="replace") as source,
        output_path.open("w", encoding=encoding) as target,
        bad_output_path.open("w", encoding=encoding) as bad_target,
    ):
        for line_no, line in enumerate(source, 1):
            if limit and input_rows >= limit:
                break

            stripped = line.strip()
            if not stripped:
                continue
            input_rows += 1

            try:
                repaired = repair_line(
                    stripped,
                    columns=columns,
                    string_fields=string_fields,
                    number_fields=number_fields,
                    keep_empty_string=keep_empty_string,
                )
                json_line = json.dumps(repaired, ensure_ascii=False, separators=(",", ":"))
                json.loads(json_line)
                target.write(json_line + "\n")
                rows += 1
            except Exception as exc:  # noqa: BLE001 - keep bad rows for manual review
                bad_rows += 1
                bad_target.write(
                    json.dumps(
                        {
                            "line_no": line_no,
                            "error": str(exc),
                            "raw": stripped,
                        },
                        ensure_ascii=False,
                    )
                    + "\n"
                )

            if progress_interval and input_rows % progress_interval == 0:
                print(f"{table_name}: input_rows={input_rows} rows={rows} bad_rows={bad_rows}")

    print(f"table={table_name}")
    print(f"input={input_path}")
    print(f"output={output_path}")
    print(f"bad_output={bad_output_path}")
    print(f"input_rows={input_rows}")
    print(f"rows={rows}")
    print(f"bad_rows={bad_rows}")
