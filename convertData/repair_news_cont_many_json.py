from __future__ import annotations

import argparse
from pathlib import Path

from repair_json_common import repair_file


TABLE_NAME = "NEWS_CONT"
COLUMNS = ["YMD", "SEQNO", "NEWSCODE", "LINENO", "CONTENT"]
STRING_FIELDS = {"YMD", "SEQNO", "NEWSCODE", "CONTENT"}
NUMBER_FIELDS = {"LINENO"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Repair malformed Oracle JSON_OBJECT export files whose names start with news_cont_."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("input"),
        help="directory containing news_cont_* files",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output"),
        help="directory for repaired JSON files",
    )
    parser.add_argument(
        "--pattern",
        default="news_cont_*",
        help="glob pattern for input files inside --input-dir",
    )
    parser.add_argument("--encoding", default="utf-8", help="input/output encoding")
    parser.add_argument("--progress-interval", type=int, default=100_000, help="progress print interval per file")
    parser.add_argument("--limit", type=int, default=0, help="stop after N input rows per file for test runs")
    parser.add_argument(
        "--keep-empty-string",
        action="store_true",
        help="keep empty values as empty string instead of null",
    )
    return parser.parse_args()


def output_path_for(input_path: Path, input_dir: Path, output_dir: Path) -> Path:
    # Preserve subdirectory structure if --input-dir contains nested folders.
    # Always write a .json extension, even when the input is .data or .txt.
    relative = input_path.relative_to(input_dir)
    return (output_dir / relative).with_suffix(".json")


def bad_output_path_for(output_path: Path, output_dir: Path) -> Path:
    # Keep bad rows under output/bad/ with the same relative path shape.
    relative = output_path.relative_to(output_dir)
    return output_dir / "bad" / relative.with_name(f"{relative.stem}.bad.json")


def main() -> None:
    args = parse_args()
    input_dir = args.input_dir
    output_dir = args.output_dir

    if not input_dir.exists():
        raise FileNotFoundError(f"input directory does not exist: {input_dir}")

    # Select every regular file whose file name starts with news_cont_ by default.
    # Example matches: news_cont_p.data, news_cont_q.json, news_cont_202607.txt
    input_files = sorted(path for path in input_dir.glob(args.pattern) if path.is_file())

    if not input_files:
        print(f"No input files matched: {input_dir / args.pattern}")
        return

    print(f"matched_files={len(input_files)}")

    # Convert files one by one using the same NEWS_CONT schema:
    # YMD, SEQNO, NEWSCODE, LINENO, CONTENT.
    for index, input_path in enumerate(input_files, start=1):
        output_path = output_path_for(input_path, input_dir, output_dir)
        bad_output_path = bad_output_path_for(output_path, output_dir)

        print(f"[{index}/{len(input_files)}] repairing {input_path} -> {output_path}")
        repair_file(
            input_path=input_path,
            output_path=output_path,
            bad_output_path=bad_output_path,
            encoding=args.encoding,
            columns=COLUMNS,
            string_fields=STRING_FIELDS,
            number_fields=NUMBER_FIELDS,
            keep_empty_string=args.keep_empty_string,
            progress_interval=args.progress_interval,
            limit=args.limit,
            table_name=f"{TABLE_NAME}:{input_path.name}",
        )


if __name__ == "__main__":
    main()
