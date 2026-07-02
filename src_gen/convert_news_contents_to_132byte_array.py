from __future__ import annotations

import argparse
import json
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_INPUT = BASE_DIR / "generated_news_collection_1gb" / "news_unified_collection_1gb.json"
DEFAULT_OUTPUT = BASE_DIR / "generated_news_collection_1gb" / "news_unified_collection_1gb_contents_array.json"
CONTENT_CHUNK_BYTES = 132


def chunk_utf8_by_bytes(text: str, limit: int) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_bytes = 0

    for ch in text:
        size = len(ch.encode("utf-8"))
        if current and current_bytes + size > limit:
            chunks.append("".join(current))
            current = [ch]
            current_bytes = size
        else:
            current.append(ch)
            current_bytes += size

    if current:
        chunks.append("".join(current))

    return chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert news.contents string to 132-byte UTF-8-safe chunk array.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--progress-interval", type=int, default=100_000)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)

    documents = 0
    total_bytes = 0
    min_chunks = 999
    max_chunks = 0
    max_chunk_bytes = 0

    with args.input.open("r", encoding="utf-8") as source, args.output.open("wb", buffering=1024 * 1024) as target:
        for line in source:
            doc = json.loads(line)
            contents = doc.get("contents")
            if not isinstance(contents, str):
                raise ValueError(f"contents is not a string at document {documents + 1}")

            chunks = chunk_utf8_by_bytes(contents, CONTENT_CHUNK_BYTES)
            doc["contents"] = chunks

            chunk_count = len(chunks)
            min_chunks = min(min_chunks, chunk_count)
            max_chunks = max(max_chunks, chunk_count)
            for chunk in chunks:
                chunk_bytes = len(chunk.encode("utf-8"))
                if chunk_bytes > CONTENT_CHUNK_BYTES:
                    raise ValueError(f"chunk exceeds {CONTENT_CHUNK_BYTES} bytes at document {documents + 1}")
                max_chunk_bytes = max(max_chunk_bytes, chunk_bytes)

            data = (json.dumps(doc, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
            target.write(data)
            total_bytes += len(data)
            documents += 1

            if args.progress_interval and documents % args.progress_interval == 0:
                print(f"documents={documents} bytes={total_bytes}")

    print(f"input_file={args.input}")
    print(f"output_file={args.output}")
    print(f"documents={documents}")
    print(f"total_bytes={total_bytes}")
    print(f"min_content_chunks={min_chunks}")
    print(f"max_content_chunks={max_chunks}")
    print(f"max_content_chunk_bytes={max_chunk_bytes}")


if __name__ == "__main__":
    main()
