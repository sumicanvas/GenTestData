from __future__ import annotations

import argparse
import calendar
import json
import random
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = BASE_DIR / "generated_news_collection_1gb"
DEFAULT_TARGET_BYTES = 1_000_000_000
CONTENT_CHUNK_BYTES = 132
DEFAULT_START_DATE = date(2023, 6, 30)
DEFAULT_END_DATE = date(2026, 6, 30)
DEFAULT_MONTHLY_MIN_ARTICLES = 10
DEFAULT_RANDOM_SEED = 20260701
KST = timezone(timedelta(hours=9))
UTC = timezone.utc

STOCKS = [
    ("005930", "삼성전자", "반도체"),
    ("000660", "SK하이닉스", "반도체"),
    ("035420", "NAVER", "인터넷"),
    ("035720", "카카오", "플랫폼"),
    ("005380", "현대차", "자동차"),
    ("000270", "기아", "자동차"),
    ("051910", "LG화학", "화학"),
    ("006400", "삼성SDI", "2차전지"),
    ("373220", "LG에너지솔루션", "2차전지"),
    ("207940", "삼성바이오로직스", "바이오"),
    ("068270", "셀트리온", "바이오"),
    ("105560", "KB금융", "금융"),
    ("055550", "신한지주", "금융"),
    ("086790", "하나금융지주", "금융"),
    ("011200", "HMM", "해운"),
    ("009830", "한화솔루션", "태양광"),
    ("003670", "포스코퓨처엠", "소재"),
    ("012450", "한화에어로스페이스", "방산"),
    ("028260", "삼성물산", "지주"),
    ("096770", "SK이노베이션", "정유"),
    ("010130", "고려아연", "비철금속"),
    ("034020", "두산에너빌리티", "원전"),
    ("042660", "한화오션", "조선"),
    ("329180", "HD현대중공업", "조선"),
    ("018260", "삼성에스디에스", "IT서비스"),
    ("032830", "삼성생명", "보험"),
    ("017670", "SK텔레콤", "통신"),
    ("030200", "KT", "통신"),
    ("066570", "LG전자", "가전"),
    ("090430", "아모레퍼시픽", "화장품"),
    ("024110", "기업은행", "은행"),
    ("316140", "우리금융지주", "금융"),
    ("086520", "에코프로", "2차전지"),
    ("247540", "에코프로비엠", "2차전지"),
    ("352820", "하이브", "엔터"),
    ("251270", "넷마블", "게임"),
    ("259960", "크래프톤", "게임"),
    ("005490", "POSCO홀딩스", "철강"),
    ("010950", "S-Oil", "정유"),
    ("011070", "LG이노텍", "부품"),
]

NEWS_SOURCES = [
    ("4", "01", "010000", "인포스탁"),
    ("P", "P3", "030000", "뉴스핌"),
    ("M", "M1", "020000", "매일경제"),
    ("F", "F2", "040000", "파이낸셜뉴스"),
    ("7", "H1", "050000", "한국경제"),
    ("9", "E1", "060000", "이데일리"),
    ("8", "MT", "070000", "머니투데이"),
    ("S", "S1", "080000", "아시아경제"),
]

TITLE_PATTERNS = [
    "{name}, {theme} 업황 회복 기대에 강세",
    "{name}, 외국인 순매수 확대 속 주가 반등",
    "{name}, 실적 개선 전망에 증권가 목표가 상향",
    "{theme} 대표주 {name}, 정책 모멘텀에 관심 집중",
    "{name}, 수급 개선과 밸류에이션 매력 부각",
    "{name}, 기관 매수세 유입에 장중 상승폭 확대",
    "{theme} 업종, {name} 중심으로 투자심리 개선",
    "{name}, 주주환원 확대 기대에 시장 주목",
    "{name}, 거래대금 증가 속 단기 저항선 돌파 시도",
    "{theme} 관련주 {name}, 실적 가시성 부각",
    "{name}, 원가 부담 완화 기대에 반등세",
    "{name}, 신규 수주와 매출 성장 기대감 확대",
]

CONTENT_OPENERS = [
    "업황 개선 기대에 장중 강세를 보였다",
    "외국인 수급이 유입되며 반등 흐름을 보였다",
    "실적 추정치 상향 기대가 주가에 반영됐다",
    "정책 모멘텀과 업종 순환매가 함께 부각됐다",
    "거래대금 증가와 기관 매수세가 확인됐다",
]

CONTENT_ANALYSES = [
    "증권가는 외국인 수급과 분기 실적 전망을 함께 확인해야 한다고 분석했다",
    "시장에서는 금리와 환율 흐름이 단기 변동성의 핵심 변수라고 평가했다",
    "전문가들은 업황 회복 속도와 비용 부담을 같이 점검할 필요가 있다고 조언했다",
    "일부 증권사는 실적 가시성이 높아지는 구간에서 재평가가 가능하다고 봤다",
    "투자자 관심은 검색량과 거래량 증가로 이어지며 업종 대표주에 집중됐다",
]

CONTENT_RISKS = [
    "다만 글로벌 경기 둔화와 원자재 가격 변동성은 확인해야 할 리스크로 꼽힌다",
    "단기 급등 부담이 남아 있어 분할 접근과 변동성 관리가 필요하다는 의견도 나왔다",
    "수급 쏠림이 완화될 경우 주가 흐름이 다시 차별화될 수 있다는 분석이다",
    "실적 발표 전까지는 기대감과 차익실현 매물이 동시에 나타날 수 있다는 평가다",
    "업종 전반의 회복 여부는 수주와 재고, 가격 지표를 통해 확인해야 한다는 설명이다",
]


def sanitize(value: str) -> str:
    return str(value).replace("\r", " ").replace("\n", " ").strip()


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


def build_html_content(index: int, source_name: str, stock: tuple[str, str, str]) -> tuple[list[str], int, int]:
    code, name, theme = stock
    opener = CONTENT_OPENERS[index % len(CONTENT_OPENERS)]
    analysis = CONTENT_ANALYSES[index % len(CONTENT_ANALYSES)]
    risk = CONTENT_RISKS[index % len(CONTENT_RISKS)]

    parts = [
        f'<div class="news"><p><strong>{name}</strong>({code})은 {theme} {opener}.</p>',
        f"<p>{analysis}.</p>",
        f"<table><tr><td>{source_name} 테스트 기사</td></tr></table>",
    ]

    target_lines = 3 + (index % 3)
    if target_lines >= 4:
        parts.append("<p><em>기관 매수세와 거래대금 증가가 이어졌고 대표주 중심 매수가 유입됐다.</em></p>")
    if target_lines >= 5:
        parts.append(f"<p><span>{risk}.</span></p>")

    content = sanitize("".join(parts) + "</div>")
    chunks = chunk_utf8_by_bytes(content, CONTENT_CHUNK_BYTES)

    if not 3 <= len(chunks) <= 5:
        raise ValueError(f"content line count out of range: index={index}, lines={len(chunks)}")

    return chunks, len(chunks), max(len(chunk.encode("utf-8")) for chunk in chunks)


def month_ranges(start: date, end: date):
    year = start.year
    month = start.month

    while (year, month) <= (end.year, end.month):
        first = date(year, month, 1)
        last = date(year, month, calendar.monthrange(year, month)[1])
        yield max(start, first), min(end, last)

        if month == 12:
            year += 1
            month = 1
        else:
            month += 1


class DateSampler:
    def __init__(self, start: date, end: date, monthly_min_articles: int, seed: int) -> None:
        if start > end:
            raise ValueError("start date must be earlier than or equal to end date")

        self.start = start
        self.end = end
        self.total_days = (end - start).days
        self.seed = seed
        self.rng = random.Random(seed)
        self.required_dates = self._build_required_dates(monthly_min_articles)
        self.day_counts: dict[str, int] = {}

    def _build_required_dates(self, monthly_min_articles: int) -> list[date]:
        required: list[date] = []
        for first, last in month_ranges(self.start, self.end):
            days = (last - first).days
            for _ in range(monthly_min_articles):
                required.append(first + timedelta(days=self.rng.randint(0, days)))
        required.extend([self.start, self.end])
        self.rng.shuffle(required)
        return required

    @property
    def required_count(self) -> int:
        return len(self.required_dates)

    def next_newscode(self, index: int) -> tuple[str, str, str]:
        if index < len(self.required_dates):
            selected = self.required_dates[index]
        else:
            selected = self.start + timedelta(days=self.rng.randint(0, self.total_days))

        ymd = selected.strftime("%Y%m%d")
        day_count = self.day_counts.get(ymd, 0)
        self.day_counts[ymd] = day_count + 1

        slot = (day_count * 7919 + self.seed) % 8_640_000
        seconds = slot // 100
        suffix = slot % 100
        hour = seconds // 3600
        minute = (seconds % 3600) // 60
        second = seconds % 60
        seqno = f"{hour:02d}{minute:02d}{second:02d}{suffix:02d}"
        newscode = ymd + seqno

        return ymd, seqno, newscode


def parse_date(value: str) -> date:
    return date.fromisoformat(value)


def newscode_to_utc_datetime(newscode: str) -> datetime:
    source_time = datetime.combine(
        date(int(newscode[0:4]), int(newscode[4:6]), int(newscode[6:8])),
        time(int(newscode[8:10]), int(newscode[10:12]), int(newscode[12:14])),
        tzinfo=KST,
    )
    return source_time.astimezone(UTC)


def iso_date_millis(value: datetime) -> str:
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def object_id_from_datetime(value: datetime, index: int) -> str:
    timestamp_hex = f"{int(value.timestamp()):08x}"
    unique_tail = f"{index & 0xFFFFFFFFFFFFFFFF:016x}"
    return timestamp_hex + unique_tail


def build_document(index: int, ymd: str, newscode: str) -> tuple[dict, int, int]:
    dgubun, kind, kind2, source_name = NEWS_SOURCES[index % len(NEWS_SOURCES)]
    primary = STOCKS[(index * 7) % len(STOCKS)]
    related_count = 1 + (index % 3)
    related = [STOCKS[((index * 7) + i) % len(STOCKS)] for i in range(related_count)]
    primary_code, primary_name, primary_theme = primary
    title = TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(name=primary_name, theme=primary_theme)
    contents, content_lines, max_chunk_bytes = build_html_content(index, source_name, primary)
    newscode_ts = newscode_to_utc_datetime(newscode)
    kind_values = [kind]
    if index % 2 == 0:
        kind_values.append(kind2)

    document = {
        "_id": {"$oid": object_id_from_datetime(newscode_ts, index)},
        "newscode_ts": {"$date": iso_date_millis(newscode_ts)},
        "title": title,
        "contents": contents,
        "dgubun": dgubun,
        "shcode": [code for code, _, _ in related],
        "kind": kind_values,
    }

    if document["_id"]["$oid"][:8] != f"{int(newscode_ts.timestamp()):08x}":
        raise ValueError("ObjectId timestamp prefix does not match newscode_ts")
    if not 1 <= len(document["kind"]) <= 2:
        raise ValueError("kind must contain one or two values")

    return document, content_lines, max_chunk_bytes


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate unified news collection Extended JSON test data.")
    parser.add_argument("--target-bytes", type=int, default=DEFAULT_TARGET_BYTES, help="output file size target")
    parser.add_argument("--min-articles", type=int, default=500, help="minimum document count")
    parser.add_argument("--start-date", type=parse_date, default=DEFAULT_START_DATE, help="inclusive source newscode start date, YYYY-MM-DD")
    parser.add_argument("--end-date", type=parse_date, default=DEFAULT_END_DATE, help="inclusive source newscode end date, YYYY-MM-DD")
    parser.add_argument("--monthly-min-articles", type=int, default=DEFAULT_MONTHLY_MIN_ARTICLES, help="minimum documents per source newscode month")
    parser.add_argument("--random-seed", type=int, default=DEFAULT_RANDOM_SEED, help="deterministic random seed")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR, help="output directory")
    parser.add_argument("--output-file", default="news_unified_collection_1gb.json", help="line-delimited Extended JSON file name")
    parser.add_argument("--progress-interval", type=int, default=50_000, help="progress print interval")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    output_path = out_dir / args.output_file

    date_sampler = DateSampler(args.start_date, args.end_date, args.monthly_min_articles, args.random_seed)
    min_articles = max(args.min_articles, date_sampler.required_count)
    bytes_written = 0
    document_count = 0
    min_source_ymd = "99999999"
    max_source_ymd = "00000000"
    min_content_lines = 99
    max_content_lines = 0
    max_chunk_bytes = 0
    max_kind_count = 0
    max_shcode_count = 0

    with output_path.open("wb", buffering=1024 * 1024) as handle:
        index = 0
        while bytes_written < args.target_bytes or document_count < min_articles:
            ymd, _, newscode = date_sampler.next_newscode(index)
            document, content_lines, chunk_bytes = build_document(index, ymd, newscode)
            line = json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n"
            data = line.encode("utf-8")
            handle.write(data)

            bytes_written += len(data)
            document_count += 1
            min_source_ymd = min(min_source_ymd, ymd)
            max_source_ymd = max(max_source_ymd, ymd)
            min_content_lines = min(min_content_lines, content_lines)
            max_content_lines = max(max_content_lines, content_lines)
            max_chunk_bytes = max(max_chunk_bytes, chunk_bytes)
            max_kind_count = max(max_kind_count, len(document["kind"]))
            max_shcode_count = max(max_shcode_count, len(document["shcode"]))

            index += 1
            if args.progress_interval and document_count % args.progress_interval == 0:
                print(f"documents={document_count} bytes={bytes_written}")

    print(f"output_file={output_path}")
    print(f"total_bytes={bytes_written}")
    print(f"document_count={document_count}")
    print(f"source_date_start={args.start_date.isoformat()}")
    print(f"source_date_end={args.end_date.isoformat()}")
    print(f"min_source_ymd={min_source_ymd}")
    print(f"max_source_ymd={max_source_ymd}")
    print(f"monthly_min_articles={args.monthly_min_articles}")
    print(f"random_seed={args.random_seed}")
    print(f"min_content_lines_if_split_132={min_content_lines}")
    print(f"max_content_lines_if_split_132={max_content_lines}")
    print(f"max_content_chunk_bytes={max_chunk_bytes}")
    print(f"max_kind_count={max_kind_count}")
    print(f"max_shcode_count={max_shcode_count}")


if __name__ == "__main__":
    main()
