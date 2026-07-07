# news_mig_500 시나리오 실행 가이드

`news_mig_500` 컬렉션을 대상으로 Atlas Search POC 시나리오를 Node.js 프로그램으로 실행하는 방법을 정리한다.

기존 `news_array_scenarios`와 동일한 10개 시나리오를 `news_mig_500` 컬렉션 기준으로 별도 폴더에 구성했다.

## 대상

```text
Database: newsdb
Collection: news_mig_500
Search Index: news_search_index
```

시나리오 프로그램 위치는 다음과 같다.

```text
kbpoc/news_mig_500_scenarios/
```

공통 실행 로직은 다음 파일에 있다.

```text
kbpoc/news_mig_500_scenarios/common.js
```

## 생성 파일

```text
news_mig_500_scenarios/common.js
news_mig_500_scenarios/scenario01_all_news.js
news_mig_500_scenarios/scenario02_news_source.js
news_mig_500_scenarios/scenario03_stock_keyword.js
news_mig_500_scenarios/scenario04_stock_source_keyword.js
news_mig_500_scenarios/scenario05_stock_only.js
news_mig_500_scenarios/scenario06_stock_source.js
news_mig_500_scenarios/scenario07_keyword.js
news_mig_500_scenarios/scenario08_source_keyword.js
news_mig_500_scenarios/scenario09_fuzzy.js
news_mig_500_scenarios/scenario10_highlight.js
news_mig_500_scenarios/README.md
```

`package.json`에는 아래 npm script가 추가되어 있다.

```text
mig500:1
mig500:2
mig500:3
mig500:4
mig500:5
mig500:6
mig500:7
mig500:8
mig500:9
mig500:10
```

## news_mig_500 문서 구조

`news_mig_500`은 migration 결과 컬렉션이므로 기존 `news_array`와 종목코드 구조가 다를 수 있다.

현재 시나리오 프로그램은 아래 구조를 기본값으로 본다.

```js
{
  _id: ObjectId(...),
  newscode_ts: 1767193200000,
  title: "...",
  contents: ["...", "...", "..."],
  dgubun: "4",
  shcodeTop: "005930",
  shcode: [
    {
      shcode: "005930",
      expcode: "A005930"
    }
  ],
  kind: ["01", "010000"]
}
```

종목코드 filter의 기본 path는 다음이다.

```text
shcode.shcode
```

만약 실제 target 구조가 아래처럼 문자열 배열이라면:

```js
{
  shcode: ["005930", "000660"]
}
```

실행 시 `--shcode-path shcode`를 추가한다.

```sh
npm run mig500:5 -- --shcode 005930 --shcode-path shcode --limit 5
```

만약 대표 종목코드인 `shcodeTop` 기준으로 검색하려면 다음처럼 실행한다.

```sh
npm run mig500:5 -- --shcode 005930 --shcode-path shcodeTop --limit 5
```

## Search Index 전제

`news_mig_500`에 `news_search_index`가 생성되어 있어야 한다.

필수 검색 필드는 다음이다.

| 필드 | Atlas Search 타입 | 용도 |
|---|---|---|
| `title` | `string`, `lucene.nori` | 제목 검색 |
| `contents` | `string`, `lucene.nori` | 본문 배열 검색 |
| `dgubun` | `token` | 뉴스구분 exact filter |
| `shcode.shcode` | `token` | 종목코드 exact filter |
| `shcodeTop` | `token` | 대표 종목코드 exact filter 선택지 |
| `kind` | `token` | kind exact filter 선택지 |
| `newscode_ts` | `date` 또는 정렬 가능한 숫자/date | 최신순 정렬 |

`newscode_ts`가 숫자 milliseconds로 저장된 경우 Atlas Search sort 동작을 위해 인덱스 mapping과 실제 타입이 맞아야 한다.

## 출력 방식

전체 시나리오는 MongoDB 쿼리 실행 전에 실제 실행되는 MQL을 먼저 출력한다.

출력 순서는 다음과 같다.

```text
실행 MQL
쿼리시작전
쿼리수행후
조회 결과 JSON
전체수행시간
```

출력 위치는 다음과 같다.

| 출력 | 위치 |
|---|---|
| 실행 MQL | stderr, 로그 파일 |
| 쿼리시작전 | stderr, 로그 파일 |
| 쿼리수행후 | stderr, 로그 파일 |
| 전체수행시간 | stderr, 로그 파일 |
| 조회 결과 JSON | stdout |

조회 결과만 파일로 저장하려면 stdout redirect를 사용한다.

```sh
npm run mig500:7 -- --query "삼성전자 실적" --limit 5 > result.json
```

## 공통 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--uri` | MongoDB 접속 문자열 | `MONGODB_URI` 환경변수 |
| `--db` | database 이름 | `newsdb` |
| `--collection` | collection 이름 | `news_mig_500` |
| `--index` | Atlas Search index 이름 | `news_search_index` |
| `--shcode-path` | 종목코드 filter path | `shcode.shcode` |
| `--limit` | 조회 건수 | `100` |
| `--dry-run` | MongoDB 접속 없이 MQL만 출력 | 비활성 |
| `--no-log` | 로그 파일 기록 비활성화 | 비활성 |
| `--help` | 사용법 출력 | 비활성 |

필수 입력값을 CLI 옵션으로 주지 않으면 프로그램이 터미널에서 값을 물어본다.

## dry-run

`--dry-run`을 사용하면 MongoDB에 접속하지 않고 실행될 MQL만 확인한다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun 4 --query "삼성전자 실적" --limit 5 --dry-run
```

출력 예시는 다음과 같다.

```js
db.news_mig_500.aggregate([
  {
    "$search": {
      "index": "news_search_index",
      "compound": {
        "must": [
          {
            "text": {
              "query": "삼성전자 실적",
              "path": [
                "title",
                "contents"
              ],
              "matchCriteria": "all"
            }
          }
        ],
        "filter": [
          {
            "equals": {
              "path": "shcode.shcode",
              "value": "005930"
            }
          },
          {
            "equals": {
              "path": "dgubun",
              "value": "4"
            }
          }
        ]
      },
      "sort": {
        "score": {
          "$meta": "searchScore"
        },
        "newscode_ts": -1
      }
    }
  },
  {
    "$limit": 5
  },
  {
    "$project": {
      "_id": 1,
      "newscode_ts": 1,
      "title": 1,
      "contents": 1,
      "dgubun": 1,
      "shcode": 1,
      "shcodeTop": 1,
      "kind": 1,
      "score": {
        "$meta": "searchScore"
      }
    }
  }
]);
```

## 시나리오 목록

| 시나리오 | npm script | 설명 | 주요 입력값 |
|---|---|---|---|
| 1 | `mig500:1` | 제목/본문 검색 후 최신순 조회 | `--query`, 기본값 `에헤라` |
| 2 | `mig500:2` | 뉴스구분 조건 조회 | `--dgubun` |
| 3 | `mig500:3` | 종목코드 + 검색어 검색 | `--shcode`, `--query` |
| 4 | `mig500:4` | 종목코드 + 뉴스구분 + 검색어 검색 | `--shcode`, `--dgubun`, `--query` |
| 5 | `mig500:5` | 종목코드 조건 조회 | `--shcode` |
| 6 | `mig500:6` | 종목코드 + 뉴스구분 조건 조회 | `--shcode`, `--dgubun` |
| 7 | `mig500:7` | 검색어 전체 검색 | `--query` |
| 8 | `mig500:8` | 뉴스구분 + 검색어 검색 | `--dgubun`, `--query` |
| 9 | `mig500:9` | Fuzzy 검색 | `--query`, `--title-boost`, `--contents-boost`, `--min-score` |
| 10 | `mig500:10` | Highlight 검색 | `--query` |

## 시나리오별 실행 명령

아래 명령은 모두 `kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

### 시나리오 1

기본 검색어 `에헤라`로 제목/본문을 검색하고 최신순으로 조회한다.

```sh
npm run mig500:1 -- --limit 5
```

검색어를 직접 지정한다.

```sh
npm run mig500:1 -- --query "삼성전자" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:1 -- --dry-run --limit 5
```

### 시나리오 2

뉴스구분 조건으로 해당 뉴스매체의 뉴스를 최신순 조회한다.

```sh
npm run mig500:2 -- --dgubun P --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:2 -- --dgubun P --dry-run --limit 5
```

### 시나리오 3

종목코드와 검색어로 검색한다.

```sh
npm run mig500:3 -- --shcode 005930 --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:3 -- --shcode 005930 --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 4

종목코드, 뉴스구분, 검색어로 검색한다.

`삼성전자 실적` + `005930` 조합은 테스트 데이터 기준 뉴스구분 `4`에서 결과가 나온다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun 4 --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun 4 --query "삼성전자 실적" --dry-run --limit 5
```

만약 `P` 뉴스구분을 사용하고 싶으면 검색어도 데이터에 맞춰야 한다.

예시는 다음과 같다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun P --query "LG이노텍 기관" --limit 5
```

### 시나리오 5

종목코드 조건으로 해당 종목의 뉴스를 최신순 조회한다.

```sh
npm run mig500:5 -- --shcode 005930 --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:5 -- --shcode 005930 --dry-run --limit 5
```

### 시나리오 6

종목코드와 뉴스구분 조건으로 뉴스를 최신순 조회한다.

```sh
npm run mig500:6 -- --shcode 005930 --dgubun P --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:6 -- --shcode 005930 --dgubun P --dry-run --limit 5
```

### 시나리오 7

검색어만 사용해 전체 뉴스에서 검색한다.

```sh
npm run mig500:7 -- --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:7 -- --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 8

뉴스구분과 검색어로 검색한다.

```sh
npm run mig500:8 -- --dgubun P --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:8 -- --dgubun P --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 9

Fuzzy 검색을 실행한다.

```sh
npm run mig500:9 -- --query "삼영전자" --limit 5
```

가중치를 조정한다.

```sh
npm run mig500:9 -- --query "삼영전자" --title-boost 3 --contents-boost 1 --limit 5
```

score 컷오프를 조정한다.

```sh
npm run mig500:9 -- --query "사성전" --min-score 1 --limit 5
```

낮은 score 결과까지 모두 확인한다.

```sh
npm run mig500:9 -- --query "사성전" --min-score 0 --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:9 -- --query "삼영전자" --dry-run --limit 5
```

### 시나리오 10

Highlight 검색을 실행한다.

```sh
npm run mig500:10 -- --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run mig500:10 -- --query "삼성전자 실적" --dry-run --limit 5
```

## 직접 실행

npm script 대신 Node.js 파일을 직접 실행할 수도 있다.

```sh
node news_mig_500_scenarios/scenario04_stock_source_keyword.js \
  --shcode 005930 \
  --dgubun 4 \
  --query "삼성전자 실적" \
  --limit 5
```

직접 실행에서도 MQL 출력, 수행시간 출력, 로그 기록 방식은 동일하다.

## 결과 저장

조회 결과 JSON만 파일로 저장한다.

```sh
npm run mig500:3 -- --shcode 005930 --query "삼성전자 실적" --limit 100 > mig500_scenario3_result.json
```

MQL과 수행시간까지 함께 파일로 저장하려면 stderr도 redirect한다.

```sh
npm run mig500:3 -- --shcode 005930 --query "삼성전자 실적" --limit 100 > mig500_scenario3_result.json 2> mig500_scenario3_log.txt
```

## 로그 파일

로그 파일은 아래 경로에 생성된다.

```text
kbpoc/news_mig_500_scenarios/logs/
```

로그 파일 기록을 끄려면 `--no-log`를 사용한다.

```sh
npm run mig500:7 -- --query "삼성전자 실적" --limit 5 --no-log
```

## 결과가 0건일 때 확인할 것

시나리오 4처럼 여러 조건을 동시에 사용하는 경우, `종목코드 + 뉴스구분 + 검색어` 조합이 실제 데이터와 맞아야 한다.

예를 들어 아래 조합은 테스트 데이터 기준 결과가 나오도록 확인한 조합이다.

```text
종목코드: 005930
뉴스구분: 4
검색어: 삼성전자 실적
```

반대로 아래 조합은 검색어와 뉴스구분이 맞지 않으면 0건이 나올 수 있다.

```text
종목코드: 005930
뉴스구분: P
검색어: 삼성전자 실적
```

`P` 뉴스구분에서 결과를 보려면 테스트 데이터에 맞는 검색어를 사용한다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun P --query "LG이노텍 기관" --limit 5
```

## 참고

`news_mig_500`이 기존 non-unified migration 결과라면 `title` 문서와 `contents` 문서가 분리되어 있을 수 있다.

이 경우 `title`, `shcode`, `contents`가 한 document에 모두 있는 unified 구조보다 검색 결과가 다르게 나올 수 있다.

통합 document 구조를 대상으로 테스트하려면 `migration_unified`로 만든 target collection을 사용하고, 실행 시 `--collection`을 해당 target으로 바꾼다.

예시는 다음과 같다.

```sh
npm run mig500:4 -- \
  --collection news_mig_500_unified \
  --shcode 005930 \
  --dgubun 4 \
  --query "삼성전자 실적" \
  --limit 5
```
