# 단일 뉴스 컬렉션 테스트 데이터 생성 정리

기존 `news_mast`, `news_jmcode`, `news_cont_p` 형태로 분리된 테스트 데이터를 MongoDB `news` 단일 컬렉션 형태로 생성했다.

## 생성 결과

출력 위치:

```text
kbpoc/generated_news_collection_1gb/
```

생성 파일:

```text
news_unified_collection_1gb.json
```

파일 형식:

```text
Line-delimited Extended JSON
Encoding: UTF-8
Document per line: 1
```

생성 결과:

| 항목 | 값 |
|---|---:|
| 파일 크기 | 1,000,000,288 bytes |
| 문서 수 | 1,494,527 |
| 날짜 범위 | 2023-06-30 ~ 2026-06-30 |
| 월 수 | 37 |
| 월별 최소 문서 수 | 1,383 |

## 생성 스크립트

```text
kbpoc/generate_news_unified_collection_1gb.py
```

재생성 명령:

```sh
python3 "/Users/sumi.ryu/Documents/opencode/kbpoc/generate_news_unified_collection_1gb.py" \
  --target-bytes 1000000000 \
  --min-articles 500 \
  --progress-interval 100000 \
  --output-file news_unified_collection_1gb.json
```

## 컬렉션 구조

생성 문서는 아래 형태를 따른다.

```js
{
  _id: ObjectId(...),
  newscode_ts: ISODate(...),
  title: "...",
  contents: "...",
  dgubun: "P",
  shcode: ["005930", "000660"],
  kind: ["P3", "030000"]
}
```

필드 설명:

| 필드 | 설명 |
|---|---|
| `_id` | `newscode_ts / 1000` 초 값을 ObjectId timestamp prefix로 사용 |
| `newscode_ts` | `newscode`를 한국시간으로 해석한 뒤 UTC ISODate로 변환 |
| `title` | 뉴스 제목 |
| `contents` | HTML 태그가 포함된 뉴스 본문 |
| `dgubun` | 뉴스 구분 |
| `shcode` | 관련 국내 주식 종목코드 배열 |
| `kind` | 뉴스 kind 값 배열, 최대 2개 |

## 날짜 처리

`newscode`는 한국시간(KST, UTC+9) 기준으로 생성된 값으로 간주했다.

예시:

```text
newscode 기준 시각: 2025-05-06 08:16:47 KST
MongoDB 저장 시각: 2025-05-05T23:16:47.000Z
```

스크립트 처리 방식:

```python
source_time = datetime.combine(..., tzinfo=KST)
newscode_ts = source_time.astimezone(UTC)
```

## ObjectId 생성 방식

요구사항의 `_id = ObjectId(newscode_ts / 1000)` 의미를 반영해 ObjectId의 앞 4바이트 timestamp 영역을 `newscode_ts`의 epoch seconds 값으로 생성했다.

같은 초에 여러 뉴스가 있을 수 있으므로 ObjectId 전체 12바이트는 아래 방식으로 구성했다.

```text
앞 4바이트: int(newscode_ts.timestamp())
뒤 8바이트: 문서 index 기반 unique 값
```

이 방식으로 `_id`의 시간 정렬 특성은 유지하면서 전체 문서의 `_id` 중복을 방지했다.

검증 결과:

```text
documents: 1,494,527
unique_ids: 1,494,527
duplicate_ids: 0
bad_timestamp_prefix: 0
```

## 샘플 문서

```json
{"_id":{"$oid":"681946df0000000000000000"},"newscode_ts":{"$date":"2025-05-05T23:16:47.000Z"},"title":"삼성전자, 반도체 업황 회복 기대에 강세","contents":"<div class=\"news\"><p><strong>삼성전자</strong>(005930)은 반도체 업황 개선 기대에 장중 강세를 보였다.</p><p>증권가는 외국인 수급과 분기 실적 전망을 함께 확인해야 한다고 분석했다.</p><table><tr><td>인포스탁 테스트 기사</td></tr></table></div>","dgubun":"4","shcode":["005930"],"kind":["01","010000"]}
```

```json
{"_id":{"$oid":"6a1f645f0000000000000001"},"newscode_ts":{"$date":"2026-06-02T23:16:47.000Z"},"title":"삼성SDI, 외국인 순매수 확대 속 주가 반등","contents":"<div class=\"news\"><p><strong>삼성SDI</strong>(006400)은 2차전지 외국인 수급이 유입되며 반등 흐름을 보였다.</p><p>시장에서는 금리와 환율 흐름이 단기 변동성의 핵심 변수라고 평가했다.</p><table><tr><td>뉴스핌 테스트 기사</td></tr></table><p><em>기관 매수세와 거래대금 증가가 이어졌고 대표주 중심 매수가 유입됐다.</em></p></div>","dgubun":"P","shcode":["006400","373220"],"kind":["P3"]}
```

## 검증 결과

생성 파일 전체를 스캔해 검증했다.

```text
file_size: 1,000,000,288
documents: 1,494,527
min_kst_ymd: 20230630
max_kst_ymd: 20260630
months: 37
min_month_count: 1383
max_month_count: 42631
bad_json: 0
bad_oid: 0
bad_kind: 0
bad_fields: 0
bad_contents_html: 0
max_kind: 2
max_shcode: 3
```

검증 항목:

| 항목 | 결과 |
|---|---|
| JSON 파싱 오류 | 없음 |
| `_id` 중복 | 없음 |
| `_id` timestamp prefix와 `newscode_ts / 1000` 일치 | 정상 |
| `kind` 필드명 소문자 적용 | 정상 |
| `Kind` 대문자 필드 잔존 | 없음 |
| `kind` 배열 최대 2개 | 정상 |
| `contents` HTML 태그 포함 | 정상 |
| 날짜 범위 | 정상 |
| 월별 최소 10건 이상 | 정상 |

## MongoDB 로딩

`mongoimport`는 `mongosh` 안이 아니라 OS 터미널에서 실행한다.

```sh
export MONGODB_URI='mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority'
```

로딩 명령:

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --collection news \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbpoc/generated_news_collection_1gb/news_unified_collection_1gb.json"
```

URI에 database 이름이 없으면 `--db newsdb`를 추가한다.

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --db newsdb \
  --collection news \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbpoc/generated_news_collection_1gb/news_unified_collection_1gb.json"
```

## 참고 사항

`news_unified_collection_1gb.json`은 약 1GB 파일이므로 GitHub에는 생성 결과 파일 자체보다 생성 스크립트와 이 문서를 올리는 것을 권장한다. 결과 파일을 버전 관리해야 한다면 Git LFS 또는 별도 오브젝트 스토리지를 사용하는 것이 적합하다.
