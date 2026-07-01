from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = BASE_DIR / "generated_utf8_1gb"
DEFAULT_TARGET_BYTES = 1_000_000_000
CONTENT_CHUNK_BYTES = 132

MAST_COLS = ["DGUBUN", "YMD", "SEQNO", "NEWSCODE", "KIND", "KIND2", "TITLE", "SHCODE"]
JMCODE_COLS = ["DGUBUN", "YMD", "SEQNO", "SHCODE", "EXPCODE", "NEWSCODE", "KIND"]
CONT_COLS = ["YMD", "SEQNO", "NEWSCODE", "LINENO", "CONTENT"]

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
    return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ").strip()


def write_row(handle, values: list[str]) -> int:
    line = "\t".join(sanitize(v) for v in values) + "\n"
    data = line.encode("utf-8")
    handle.write(data)
    return len(data)


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


def build_html_content(index: int, title: str, source_name: str, stock: tuple[str, str, str]) -> list[str]:
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

    content = "".join(parts) + "</div>"
    chunks = chunk_utf8_by_bytes(content, CONTENT_CHUNK_BYTES)

    if not 3 <= len(chunks) <= 5:
        raise ValueError(f"content line count out of range: index={index}, lines={len(chunks)}, bytes={len(content.encode('utf-8'))}")

    return chunks


def article_values(index: int):
    dgubun, kind, kind2, source_name = NEWS_SOURCES[index % len(NEWS_SOURCES)]
    primary = STOCKS[(index * 7) % len(STOCKS)]
    related_count = 1 + (index % 3)
    related = [STOCKS[((index * 7) + i) % len(STOCKS)] for i in range(related_count)]
    primary_code, primary_name, primary_theme = primary
    title = TITLE_PATTERNS[index % len(TITLE_PATTERNS)].format(name=primary_name, theme=primary_theme)

    published_at = datetime(2026, 6, 25, 15, 30, 0) - timedelta(seconds=index)
    ymd = published_at.strftime("%Y%m%d")
    seqno = published_at.strftime("%H%M%S") + f"{index % 100:02d}"
    newscode = ymd + seqno
    content_chunks = build_html_content(index, title, source_name, primary)

    return dgubun, ymd, seqno, newscode, kind, kind2, title, primary_code, related, content_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate KB news UTF-8 tab-delimited test data.")
    parser.add_argument("--target-bytes", type=int, default=DEFAULT_TARGET_BYTES, help="combined output size target")
    parser.add_argument("--min-articles", type=int, default=500, help="minimum news_mast article rows")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUT_DIR, help="output directory")
    parser.add_argument("--progress-interval", type=int, default=50_000, help="progress print interval")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out_dir = args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    mast_path = out_dir / "news_mast_utf8_tab.csv"
    jmcode_path = out_dir / "news_jmcode_utf8_tab.csv"
    cont_path = out_dir / "news_cont_p_utf8_tab.csv"

    bytes_written = 0
    article_count = 0
    jmcode_count = 0
    cont_count = 0
    max_content_bytes = 0
    min_content_lines = 99
    max_content_lines = 0

    with (
        mast_path.open("wb", buffering=1024 * 1024) as mast,
        jmcode_path.open("wb", buffering=1024 * 1024) as jmcode,
        cont_path.open("wb", buffering=1024 * 1024) as cont,
    ):
        bytes_written += write_row(mast, MAST_COLS)
        bytes_written += write_row(jmcode, JMCODE_COLS)
        bytes_written += write_row(cont, CONT_COLS)

        index = 0
        while bytes_written < args.target_bytes or article_count < args.min_articles:
            dgubun, ymd, seqno, newscode, kind, kind2, title, primary_code, related, content_chunks = article_values(index)

            bytes_written += write_row(mast, [dgubun, ymd, seqno, newscode, kind, kind2, title, primary_code])
            article_count += 1

            for code, _, _ in related:
                bytes_written += write_row(jmcode, [dgubun, ymd, seqno, code, "A" + code, newscode, kind])
                jmcode_count += 1

            line_count = len(content_chunks)
            min_content_lines = min(min_content_lines, line_count)
            max_content_lines = max(max_content_lines, line_count)
            for line_no, chunk in enumerate(content_chunks, start=1):
                chunk_bytes = len(chunk.encode("utf-8"))
                max_content_bytes = max(max_content_bytes, chunk_bytes)
                bytes_written += write_row(cont, [ymd, seqno, newscode, str(line_no), chunk])
                cont_count += 1

            index += 1
            if args.progress_interval and article_count % args.progress_interval == 0:
                print(f"articles={article_count} bytes={bytes_written}")

    print(f"output_dir={out_dir}")
    print(f"total_bytes={bytes_written}")
    print(f"news_mast_rows={article_count}")
    print(f"news_jmcode_rows={jmcode_count}")
    print(f"news_cont_p_rows={cont_count}")
    print(f"min_content_lines={min_content_lines}")
    print(f"max_content_lines={max_content_lines}")
    print(f"max_content_bytes={max_content_bytes}")
    print(f"mast_file={mast_path}")
    print(f"jmcode_file={jmcode_path}")
    print(f"cont_file={cont_path}")


if __name__ == "__main__":
    main()
