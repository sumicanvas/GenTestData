# news_array 시나리오별 Node.js 실행 프로그램

`news_array` 컬렉션의 Atlas Search MQL을 시나리오별 Node.js 프로그램으로 실행하기 위한 스크립트다.

## 전제

Node.js와 npm이 필요하다. 현재 확인한 로컬 환경은 다음과 같다.

```text
node v26.0.0
npm 11.12.1
```

MongoDB Node.js Driver는 `kbpoc/package.json`에 정의되어 있으며 아래 명령으로 설치한다.

```sh
npm install
```

Atlas 접속 문자열을 환경변수로 설정한다.

```sh
export MONGODB_URI='mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority'
```

기본값:

| 옵션 | 기본값 |
|---|---|
| `--db` | `newsdb` |
| `--collection` | `news_array` |
| `--index` | `news_search_index` |
| `--limit` | `100` |

## 공통 옵션

모든 시나리오 프로그램에서 아래 옵션을 사용할 수 있다.

```text
--uri <mongodb-uri>       MONGODB_URI 대신 직접 URI 전달
--db <database>           database 이름
--collection <collection> collection 이름
--index <search-index>    Atlas Search index 이름
--limit <number>          조회 건수
--dry-run                 MongoDB 접속 없이 aggregation pipeline만 출력
--help                    도움말 출력
```

필수 입력값을 CLI 옵션으로 주지 않으면 프로그램이 터미널에서 값을 물어본다.

## 실행 방법

`kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

직접 실행:

```sh
node news_array_scenarios/scenario01_all_news.js --limit 5
```

npm script 실행:

```sh
npm run scenario:1 -- --limit 5
```

파이프라인만 확인:

```sh
node news_array_scenarios/scenario07_keyword.js --query "삼성전자 실적" --limit 5 --dry-run
```

## 시나리오 목록

| 시나리오 | 파일 | 입력값 |
|---|---|---|
| 1 | `scenario01_all_news.js` | 없음 |
| 2 | `scenario02_news_source.js` | `--dgubun` |
| 3 | `scenario03_stock_keyword.js` | `--shcode`, `--query` |
| 4 | `scenario04_stock_source_keyword.js` | `--shcode`, `--dgubun`, `--query` |
| 5 | `scenario05_stock_only.js` | `--shcode` |
| 6 | `scenario06_stock_source.js` | `--shcode`, `--dgubun` |
| 7 | `scenario07_keyword.js` | `--query` |
| 8 | `scenario08_source_keyword.js` | `--dgubun`, `--query` |
| 9 | `scenario09_fuzzy.js` | `--query` |
| 10 | `scenario10_highlight.js` | `--query` |

## 시나리오별 실행 예시

### 시나리오 1

전체 뉴스 최신순 조회.

```sh
npm run scenario:1 -- --limit 5
```

### 시나리오 2

뉴스구분 조건으로 전체 뉴스 조회.

```sh
npm run scenario:2 -- --dgubun P --limit 5
```

### 시나리오 3

종목코드와 검색어로 검색.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --limit 5
```

### 시나리오 4

종목코드, 뉴스구분, 검색어로 검색.

```sh
npm run scenario:4 -- --shcode 005930 --dgubun P --query "삼성전자 실적" --limit 5
```

### 시나리오 5

종목코드 조건으로 전체 뉴스 조회.

```sh
npm run scenario:5 -- --shcode 005930 --limit 5
```

### 시나리오 6

종목코드와 뉴스구분 조건으로 전체 뉴스 조회.

```sh
npm run scenario:6 -- --shcode 005930 --dgubun P --limit 5
```

### 시나리오 7

검색어만 사용해 전체 검색.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5
```

### 시나리오 8

뉴스구분과 검색어로 검색.

```sh
npm run scenario:8 -- --dgubun P --query "삼성전자 실적" --limit 5
```

### 시나리오 9

Fuzzy 검색. `title`과 `contents`를 모두 `should`로 검색하고 `title`에 더 높은 가중치를 준다.

```sh
npm run scenario:9 -- --query "삼영전자" --limit 5
```

가중치를 조정할 수도 있다.

```sh
npm run scenario:9 -- --query "삼영전자" --title-boost 3 --contents-boost 1 --limit 5
```

### 시나리오 10

Highlight 검색.

```sh
npm run scenario:10 -- --query "삼성전자 실적" --limit 5
```

## 정렬 기준

검색어가 없는 시나리오는 최신순만 사용한다.

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

## 참고

결과는 JSON으로 출력된다. 대량 결과를 파일로 저장하려면 shell redirect를 사용할 수 있다.

```sh
npm run scenario:7 -- --query "삼성전자" --limit 100 > result.json
```

Atlas Search index가 `READY` 상태가 아니면 `$search` 쿼리가 실패할 수 있다.
