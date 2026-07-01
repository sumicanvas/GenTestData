#  뉴스 테스트 데이터 생성 정리

`kbtestdata` 폴더의 고객 샘플 엑셀과 `create_news_*.txt` 테이블 정의를 참고해 MongoDB 로딩용 UTF-8 탭 구분 테스트 데이터를 생성했다.

## 생성 결과

출력 위치:

```text
kbtestdata/generated_utf8_1gb/
```

파일 형식:

```text
Encoding: UTF-8
Delimiter: Tab (\t)
Header: 있음
```

생성 파일:TESTDATA_GENERATION

| 파일 | 대상 컬렉션 | 데이터 건수 | 파일 크기 |
|---|---|---:|---:|
| `news_mast_utf8_tab.csv` | `news_mast` | 1,245,059 | 144,250,485 bytes |
| `news_jmcode_utf8_tab.csv` | `news_jmcode` | 2,490,117 | 136,956,481 bytes |
| `news_cont_p_utf8_tab.csv` | `news_cont_p` | 4,980,235 | 718,793,152 bytes |

전체 크기:

```text
1,000,000,118 bytes
```

## 참고 파일

입력 참고 자료:

| 파일 | 용도 |
|---|---|
| `news_mast.xlsx` | 뉴스 제목 샘플 |
| `news_jmcode.xlsx` | 뉴스별 종목코드 샘플 |
| `news_cont_p.xlsx` | 뉴스 본문 라인 분할 샘플 |
| `create_news_mast.txt` | `NEWS_MAST` 테이블 구조 |
| `create_news_jmcode.txt` | `NEWS_JMCODE` 테이블 구조 |
| `create_news_cont_p.txt` | `NEWS_CONT_P` 테이블 구조 |

생성 스크립트:

```text
kbtestdata/generate_kb_news_testdata_1gb.py
```

## 테이블 매핑

### news_mast

`create_news_mast.txt` 기준 컬럼 순서로 생성했다.

```text
DGUBUN	YMD	SEQNO	NEWSCODE	KIND	KIND2	TITLE	SHCODE
```

샘플:

```text
DGUBUN	YMD	SEQNO	NEWSCODE	KIND	KIND2	TITLE	SHCODE
4	20250506	08164701	2025050608164701	01	010000	삼성전자, 반도체 업황 회복 기대에 강세	005930
P	20260603	08164701	2026060308164701	P3	030000	삼성SDI, 외국인 순매수 확대 속 주가 반등	006400
```

### news_jmcode

`create_news_jmcode.txt` 기준 컬럼 순서로 생성했다.

```text
DGUBUN	YMD	SEQNO	SHCODE	EXPCODE	NEWSCODE	KIND
```

기사 1건에 종목코드 1~3개를 연결했다.

```python
related_count = 1 + (index % 3)
```

따라서 `news_jmcode` 건수는 `news_mast`보다 많다. 평균적으로 기사 1건당 약 2개 종목코드가 매핑된다.

### news_cont_p

`create_news_cont_p.txt` 기준 컬럼 순서로 생성했다.

```text
YMD	SEQNO	NEWSCODE	LINENO	CONTENT
```

본문 생성 규칙:

| 항목 | 규칙 |
|---|---|
| 연결 키 | `YMD`, `SEQNO`, `NEWSCODE` |
| 라인 번호 | `LINENO` 1부터 순차 증가 |
| 라인 수 | 기사 1건당 3~5개 |
| 본문 길이 | `CONTENT` 1개 row당 최대 132 bytes |
| 본문 형식 | HTML 태그 포함 |

본문에는 앞, 중간, 뒤에 HTML 태그가 포함되도록 생성했다.

예시 태그:

```html
<div class="news"><p><strong>삼성전자</strong>(005930)은 반도체 업황 개선 기대에 장중 강세를 보였다.</p>
<table><tr><td>인포스탁 테스트 기사</td></tr></table></div>
```

## 키 관계

뉴스 제목, 종목코드, 본문은 아래 키로 연결된다.

```text
YMD + SEQNO + NEWSCODE
```

`news_mast`의 기본 식별자는 Oracle DDL 기준으로 `DGUBUN`, `YMD`, `SEQNO`이다.

`news_cont_p`는 `YMD`, `SEQNO`, `NEWSCODE`, `LINENO` 조합으로 본문 라인을 구분한다.

## 데이터 생성 방식

1GB 수준의 테스트 데이터를 맞추기 위해 `news_mast` 200건 고정이 아니라 전체 크기 기준으로 기사 수를 늘렸다.

기사 날짜는 `2023-06-30`부터 `2026-06-30`까지 랜덤으로 분산 생성했다. 월별 검색/정렬 테스트를 위해 모든 월에 최소 10건 이상이 생성되도록 먼저 보장용 날짜 풀을 만든 뒤, 나머지 기사는 전체 기간에서 랜덤으로 선택한다.

`SEQNO`는 날짜별 내부 카운터를 사용해 같은 날짜 안에서 중복되지 않도록 생성한다. `NEWSCODE`는 기존 규칙대로 `YMD + SEQNO`로 생성한다.

```python
selected = start + timedelta(days=rng.randint(0, total_days))
ymd = selected.strftime("%Y%m%d")
seqno = f"{hour:02d}{minute:02d}{second:02d}{suffix:02d}"
newscode = ymd + seqno
```

국내 주식 종목코드는 스크립트의 `STOCKS` 목록에서 순환 선택했다.

예시 종목:

```text
005930 삼성전자
000660 SK하이닉스
035420 NAVER
035720 카카오
005380 현대차
000270 기아
051910 LG화학
006400 삼성SDI
373220 LG에너지솔루션
207940 삼성바이오로직스
```

## 재생성 방법

기본 1GB 생성:

```sh
python3 "/Users/sumi.ryu/Documents/opencode/kbtestdata/generate_kb_news_testdata_1gb.py"
```

명시적으로 1GB 생성:

```sh
python3 "/Users/sumi.ryu/Documents/opencode/kbtestdata/generate_kb_news_testdata_1gb.py" \
  --target-bytes 1000000000 \
  --min-articles 500 \
  --start-date 2023-06-30 \
  --end-date 2026-06-30 \
  --monthly-min-articles 10 \
  --progress-interval 100000
```

작은 샘플만 생성해 검증할 때:

```sh
python3 "/Users/sumi.ryu/Documents/opencode/kbtestdata/generate_kb_news_testdata_1gb.py" \
  --target-bytes 100000 \
  --min-articles 500 \
  --progress-interval 0
```

## 검증 결과

생성 후 검증한 결과:

```text
min_ymd: 20230630
max_ymd: 20260630
months: 37
min_month_count: 1160
max_content_bytes: 132
min_lines_per_article: 3
max_lines_per_article: 5
key_dupes: 0
newscode_bad: 0
bad_content_rows: 0
bad_article_groups: 0
```

검증한 항목:

| 항목 | 결과 |
|---|---|
| `CONTENT` 132 bytes 초과 여부 | 없음 |
| 기사별 `LINENO` 3~5개 조건 | 정상 |
| 날짜 범위 `2023-06-30`~`2026-06-30` | 정상 |
| 월별 최소 10건 이상 | 정상 |
| `DGUBUN + YMD + SEQNO` 중복 | 없음 |
| `NEWSCODE = YMD + SEQNO` | 정상 |
| 탭 구분 컬럼 수 | 정상 |
| UTF-8 파일 생성 | 정상 |

## MongoDB Atlas 로딩

`mongoimport`는 `mongosh` 안에서 실행하지 않고 OS 터미널에서 실행해야 한다.

접속 문자열 예시:

```sh
export MONGODB_URI='mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority'
```

`news_mast` 로딩:

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --collection news_mast \
  --type tsv \
  --headerline \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbtestdata/generated_utf8_1gb/news_mast_utf8_tab.csv"
```

`news_jmcode` 로딩:

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --collection news_jmcode \
  --type tsv \
  --headerline \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbtestdata/generated_utf8_1gb/news_jmcode_utf8_tab.csv"
```

`news_cont_p` 로딩:

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --collection news_cont_p \
  --type tsv \
  --headerline \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbtestdata/generated_utf8_1gb/news_cont_p_utf8_tab.csv"
```

URI에 database 이름이 없으면 `--db newsdb`를 추가한다.

## 참고 사항

`news_mast_utf8_tab.csv`는 약 124만 행이라 Microsoft Excel 행 제한인 1,048,576행을 초과한다. Excel에서 전체 파일을 열 수 없어도 TSV 구조 자체는 정상이다.

GitHub에는 1GB 데이터 파일 자체를 올리기보다 생성 스크립트와 이 문서를 올리는 것을 권장한다. 대용량 결과 파일은 Git LFS 또는 별도 스토리지 사용을 권장한다.
