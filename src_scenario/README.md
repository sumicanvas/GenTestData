# news_array 시나리오별 Node.js 실행 가이드

`news_array` 컬렉션의 Atlas Search 시나리오를 Node.js 프로그램으로 실행하기 위한 정리 문서다.

## 생성 파일

Node.js 프로그램 위치:

```text
kbpoc/news_array_scenarios/
```

공통 유틸:

```text
kbpoc/news_array_scenarios/common.js
```

시나리오별 프로그램:

| 시나리오 | 파일 | 설명 |
|---|---|---|
| 1 | `scenario01_all_news.js` | 전체 뉴스 최신순 조회 |
| 2 | `scenario02_news_source.js` | 뉴스구분 조건 조회 |
| 3 | `scenario03_stock_keyword.js` | 종목코드 + 검색어 검색 |
| 4 | `scenario04_stock_source_keyword.js` | 종목코드 + 뉴스구분 + 검색어 검색 |
| 5 | `scenario05_stock_only.js` | 종목코드 조건 조회 |
| 6 | `scenario06_stock_source.js` | 종목코드 + 뉴스구분 조건 조회 |
| 7 | `scenario07_keyword.js` | 검색어 전체 검색 |
| 8 | `scenario08_source_keyword.js` | 뉴스구분 + 검색어 검색 |
| 9 | `scenario09_fuzzy.js` | Fuzzy 검색 |
| 10 | `scenario10_highlight.js` | Highlight 검색 |

Node 프로젝트 파일:

```text
kbpoc/package.json
kbpoc/package-lock.json
```

## 실행 환경

확인한 로컬 환경:

```text
node v26.0.0
npm 11.12.1
```

의존성:

```text
mongodb Node.js Driver
```

설치:

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
npm install
```

## 접속 정보 설정

Atlas 접속 문자열을 환경변수로 설정한다.

```sh
export MONGODB_URI='mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority'
```

## 공통 기본값

| 옵션 | 기본값 |
|---|---|
| `--db` | `newsdb` |
| `--collection` | `news_array` |
| `--index` | `news_search_index` |
| `--limit` | `100` |

공통 옵션:

```text
--uri <mongodb-uri>       MONGODB_URI 대신 직접 URI 전달
--db <database>           database 이름
--collection <collection> collection 이름
--index <search-index>    Atlas Search index 이름
--limit <number>          조회 건수
--dry-run                 MongoDB 접속 없이 aggregation pipeline만 출력
--no-log                  로그 파일 기록 비활성화
--help                    도움말 출력
```

필수 입력값을 CLI 옵션으로 주지 않으면 프로그램이 터미널에서 값을 물어본다.

## 정렬 기준

검색어가 없는 시나리오는 최신순 정렬만 사용한다.

```js
sort: {
  newscode_ts: -1
}
```

검색어가 있는 시나리오는 score 1차, 최신순 2차 정렬을 사용한다.

```js
sort: {
  score: { $meta: "searchScore" },
  newscode_ts: -1
}
```

## 수행시간과 로그

각 프로그램은 쿼리 수행 전/후 시간을 화면에 출력한다.

예시:

```text
쿼리시작전: 2026-07-03T06:56:32.745Z db=newsdb collection=news_array limit=5
쿼리수행후: 2026-07-03T06:56:33.128Z rows=5
전체수행시간: 0.38 초
```

화면 출력 방식:

| 출력 | 위치 |
|---|---|
| 쿼리 시작 전/수행 후 시간, 전체수행시간 | stderr |
| 조회 결과 JSON | stdout |

로그 파일 위치:

```text
kbpoc/news_array_scenarios/logs/
```

시나리오별 로그 파일 예시:

```text
news_array_scenarios/logs/시나리오_7.log
```

로그 파일에는 쿼리 시작 전 시각, 쿼리 수행 후 시각, 조회 건수, 전체수행시간이 남는다.

로그 파일 기록을 끄려면 `--no-log`를 사용한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5 --no-log
```

## 시나리오별 실행 명령어

아래 명령은 모두 `kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

### 시나리오 1

전체 뉴스 최신순 조회.

```sh
npm run scenario:1 -- --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario01_all_news.js --limit 5
```

### 시나리오 2

뉴스구분 조건으로 해당 뉴스매체 전체 뉴스 조회.

```sh
npm run scenario:2 -- --dgubun P --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario02_news_source.js --dgubun P --limit 5
```

### 시나리오 3

종목코드 + 검색어 검색.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario03_stock_keyword.js --shcode 005930 --query "삼성전자 실적" --limit 5
```

### 시나리오 4

종목코드 + 뉴스구분 + 검색어 검색.

```sh
npm run scenario:4 -- --shcode 005930 --dgubun P --query "삼성전자 실적" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario04_stock_source_keyword.js --shcode 005930 --dgubun P --query "삼성전자 실적" --limit 5
```

### 시나리오 5

종목코드 조건으로 해당 종목 전체 뉴스 조회.

```sh
npm run scenario:5 -- --shcode 005930 --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario05_stock_only.js --shcode 005930 --limit 5
```

### 시나리오 6

종목코드 + 뉴스구분 조건으로 전체 뉴스 조회.

```sh
npm run scenario:6 -- --shcode 005930 --dgubun P --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario06_stock_source.js --shcode 005930 --dgubun P --limit 5
```

### 시나리오 7

검색어만 사용해 전체 뉴스 검색.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario07_keyword.js --query "삼성전자 실적" --limit 5
```

### 시나리오 8

뉴스구분 + 검색어 검색.

```sh
npm run scenario:8 -- --dgubun P --query "삼성전자 실적" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario08_source_keyword.js --dgubun P --query "삼성전자 실적" --limit 5
```

### 시나리오 9

Fuzzy 검색.

```sh
npm run scenario:9 -- --query "삼영전자" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario09_fuzzy.js --query "삼영전자" --limit 5
```

title/contents 가중치를 조정할 수 있다.

```sh
npm run scenario:9 -- --query "삼영전자" --title-boost 3 --contents-boost 1 --limit 5
```

시나리오 9는 `title`과 `contents`를 모두 `should`로 검색하고 `title`에 더 높은 가중치를 준다.

```js
score: {
  boost: {
    value: 5
  }
}
```

### 시나리오 10

Highlight 검색.

```sh
npm run scenario:10 -- --query "삼성전자 실적" --limit 5
```

직접 실행:

```sh
node news_array_scenarios/scenario10_highlight.js --query "삼성전자 실적" --limit 5
```

## dry-run 예시

MongoDB에 접속하지 않고 생성되는 aggregation pipeline만 확인한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5 --dry-run
```

시나리오 9 pipeline 확인:

```sh
npm run scenario:9 -- --query "삼영전자" --limit 5 --dry-run
```

## 도움말 확인

각 시나리오 프로그램은 `--help`를 지원한다.

```sh
npm run scenario:3 -- --help
```

직접 실행:

```sh
node news_array_scenarios/scenario03_stock_keyword.js --help
```

## 결과 저장

결과는 JSON으로 출력된다. 파일로 저장하려면 redirect를 사용한다.

```sh
npm run scenario:7 -- --query "삼성전자" --limit 100 > scenario7_result.json
```

쿼리 시간과 `전체수행시간`은 stderr로 출력되므로, 위처럼 stdout만 redirect하면 결과 JSON만 파일에 저장된다.

결과와 수행 로그를 모두 각각 파일로 저장하려면 아래처럼 실행한다.

```sh
npm run scenario:7 -- --query "삼성전자" --limit 100 > scenario7_result.json 2> scenario7_time.log
```

## GitHub 업로드 참고

GitHub에는 아래 파일을 올리면 된다.

```text
package.json
package-lock.json
news_array_scenarios/common.js
news_array_scenarios/scenario01_all_news.js
news_array_scenarios/scenario02_news_source.js
news_array_scenarios/scenario03_stock_keyword.js
news_array_scenarios/scenario04_stock_source_keyword.js
news_array_scenarios/scenario05_stock_only.js
news_array_scenarios/scenario06_stock_source.js
news_array_scenarios/scenario07_keyword.js
news_array_scenarios/scenario08_source_keyword.js
news_array_scenarios/scenario09_fuzzy.js
news_array_scenarios/scenario10_highlight.js
news_array_scenarios/README.md
NEWS_ARRAY_NODE_SCENARIOS.md
```

올리지 말아야 할 것:

```text
node_modules/
.env
MONGODB_URI가 포함된 파일
news_array_scenarios/logs/
```

`node_modules/`는 `.gitignore`에 추가되어 있다.
