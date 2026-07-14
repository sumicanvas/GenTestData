from __future__ import annotations

from repair_json_common import parse_args, repair_file


TABLE_NAME = "NEWS_JMCODE"
COLUMNS = ["DGUBUN", "YMD", "SEQNO", "SHCODE", "EXPCODE", "NEWSCODE", "KIND"]
STRING_FIELDS = set(COLUMNS)
NUMBER_FIELDS: set[str] = set()


def main() -> None:
    args = parse_args(
        description="Repair malformed Oracle JSON_OBJECT export for NEWS_JMCODE.",
    )
    repair_file(
        input_path=args.input,
        output_path=args.output,
        bad_output_path=args.bad_output,
        encoding=args.encoding,
        columns=COLUMNS,
        string_fields=STRING_FIELDS,
        number_fields=NUMBER_FIELDS,
        keep_empty_string=args.keep_empty_string,
        progress_interval=args.progress_interval,
        limit=args.limit,
        table_name=TABLE_NAME,
    )


if __name__ == "__main__":
    main()
