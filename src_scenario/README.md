# news_array 시나리오 실행 가이드

`news_array` 컬렉션의 Atlas Search POC 시나리오를 Node.js 프로그램으로 실행하는 방법을 정리한다.

## 대상

```text
Database: newsdb
Collection: news_array
Search Index: news_search_index
```

시나리오 프로그램 위치는 다음과 같다.

```text
kbpoc/news_array_scenarios/
```

공통 실행 로직은 다음 파일에 있다.

```text
kbpoc/news_array_scenarios/common.js
```

## 변경된 출력 방식

전체 시나리오에서 MongoDB 쿼리 실행 전에 실제 실행되는 MQL을 먼저 출력한다.

출력 순서는 다음과 같다.

```text
실행 MQL
쿼리시작전
쿼리수행후
조회 결과 JSON
전체수행시간
```

실제 실행 시 출력 위치는 다음과 같다.

| 출력 | 위치 |
|---|---|
| 실행 MQL | stderr, 로그 파일 |
| 쿼리시작전 | stderr, 로그 파일 |
| 쿼리수행후 | stderr, 로그 파일 |
| 전체수행시간 | stderr, 로그 파일 |
| 조회 결과 JSON | stdout |

조회 결과만 파일로 저장할 때는 stdout redirect를 사용한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5 > result.json
```

이 경우 MQL과 수행시간은 stderr에 출력되므로 `result.json`에는 조회 결과 JSON만 저장된다.

## MQL 출력 예시

시나리오 실행 시 `쿼리시작전` 로그보다 먼저 아래 형태의 MQL이 출력된다.

```js
실행 MQL:
db.news_array.aggregate([
  {
    "$search": {
      "index": "news_search_index",
      "text": {
        "query": "에헤라",
        "path": [
          "title",
          "contents"
        ]
      },
      "sort": {
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
      "dgubun": 1,
      "shcode": 1,
      "kind": 1
    }
  }
]);
쿼리시작전: 2026-07-06T00:00:00.000Z db=newsdb collection=news_array limit=5
```

## 설치

`kbpoc` 디렉토리에서 의존성을 설치한다.

```sh
npm install
```

## 접속 정보

Atlas 접속 문자열을 환경변수로 설정한다.

```sh
export MONGODB_URI='mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority'
```

명령 실행 시 `--uri` 옵션으로 직접 전달할 수도 있다.

```sh
npm run scenario:1 -- --uri 'mongodb+srv://<user>:<password>@<cluster-url>/newsdb?retryWrites=true&w=majority' --limit 5
```

## 공통 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--uri` | MongoDB 접속 문자열 | `MONGODB_URI` 환경변수 |
| `--db` | database 이름 | `newsdb` |
| `--collection` | collection 이름 | `news_array` |
| `--index` | Atlas Search index 이름 | `news_search_index` |
| `--limit` | 조회 건수 | `100` |
| `--dry-run` | MongoDB 접속 없이 MQL만 출력 | 비활성 |
| `--no-log` | 로그 파일 기록 비활성화 | 비활성 |
| `--help` | 사용법 출력 | 비활성 |

필수 입력값을 CLI 옵션으로 주지 않으면 프로그램이 터미널에서 값을 물어본다.

## dry-run

`--dry-run`을 사용하면 MongoDB에 접속하지 않고 실행될 MQL만 확인한다.

```sh
npm run scenario:1 -- --dry-run --limit 5
```

출력 예시는 다음과 같다.

```js
db.news_array.aggregate([
  {
    "$search": {
      "index": "news_search_index",
      "text": {
        "query": "에헤라",
        "path": [
          "title",
          "contents"
        ]
      },
      "sort": {
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
      "dgubun": 1,
      "shcode": 1,
      "kind": 1
    }
  }
]);
```

## 시나리오 목록

| 시나리오 | npm script | 설명 | 주요 입력값 |
|---|---|---|---|
| 1 | `scenario:1` | 제목/본문 검색 후 최신순 조회 | `--query`, 기본값 `에헤라` |
| 2 | `scenario:2` | 뉴스구분 조건 조회 | `--dgubun` |
| 3 | `scenario:3` | 종목코드 + 검색어 검색 | `--shcode`, `--query` |
| 4 | `scenario:4` | 종목코드 + 뉴스구분 + 검색어 검색 | `--shcode`, `--dgubun`, `--query` |
| 5 | `scenario:5` | 종목코드 조건 조회 | `--shcode` |
| 6 | `scenario:6` | 종목코드 + 뉴스구분 조건 조회 | `--shcode`, `--dgubun` |
| 7 | `scenario:7` | 검색어 전체 검색 | `--query` |
| 8 | `scenario:8` | 뉴스구분 + 검색어 검색 | `--dgubun`, `--query` |
| 9 | `scenario:9` | Fuzzy 검색 | `--query`, `--title-boost`, `--contents-boost`, `--min-score` |
| 10 | `scenario:10` | Highlight 검색 | `--query` |

## 시나리오별 실행 명령

아래 명령은 모두 `kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

### 시나리오 1

기본 검색어 `에헤라`로 제목/본문을 검색하고 최신순으로 조회한다.

```sh
npm run scenario:1 -- --limit 5
```

검색어를 직접 지정한다.

```sh
npm run scenario:1 -- --query "삼성전자" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:1 -- --dry-run --limit 5
```

### 시나리오 2

뉴스구분 조건으로 해당 뉴스매체의 뉴스를 최신순 조회한다.

```sh
npm run scenario:2 -- --dgubun P --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:2 -- --dgubun P --dry-run --limit 5
```

### 시나리오 3

종목코드와 검색어로 검색한다.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 4

종목코드, 뉴스구분, 검색어로 검색한다.

```sh
npm run scenario:4 -- --shcode 005930 --dgubun P --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:4 -- --shcode 005930 --dgubun P --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 5

종목코드 조건으로 해당 종목의 뉴스를 최신순 조회한다.

```sh
npm run scenario:5 -- --shcode 005930 --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:5 -- --shcode 005930 --dry-run --limit 5
```

### 시나리오 6

종목코드와 뉴스구분 조건으로 뉴스를 최신순 조회한다.

```sh
npm run scenario:6 -- --shcode 005930 --dgubun P --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:6 -- --shcode 005930 --dgubun P --dry-run --limit 5
```

### 시나리오 7

검색어만 사용해 전체 뉴스에서 검색한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 8

뉴스구분과 검색어로 검색한다.

```sh
npm run scenario:8 -- --dgubun P --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:8 -- --dgubun P --query "삼성전자 실적" --dry-run --limit 5
```

### 시나리오 9

Fuzzy 검색을 실행한다.

```sh
npm run scenario:9 -- --query "삼영전자" --limit 5
```

가중치를 조정한다.

```sh
npm run scenario:9 -- --query "삼영전자" --title-boost 3 --contents-boost 1 --limit 5
```

score 컷오프를 조정한다.

```sh
npm run scenario:9 -- --query "사성전" --min-score 1 --limit 5
```

낮은 score 결과까지 모두 확인한다.

```sh
npm run scenario:9 -- --query "사성전" --min-score 0 --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:9 -- --query "삼영전자" --dry-run --limit 5
```

### 시나리오 10

Highlight 검색을 실행한다.

```sh
npm run scenario:10 -- --query "삼성전자 실적" --limit 5
```

MQL만 확인한다.

```sh
npm run scenario:10 -- --query "삼성전자 실적" --dry-run --limit 5
```

## 로그 파일

로그 파일은 아래 경로에 생성된다.

```text
kbpoc/news_array_scenarios/logs/
```

로그에는 실행 MQL, 쿼리 시작 시각, 쿼리 종료 시각, 조회 건수, 전체수행시간이 기록된다.

로그 파일 기록을 끄려면 `--no-log`를 사용한다.

```sh
npm run scenario:7 -- --query "삼성전자 실적" --limit 5 --no-log
```

## 직접 실행

npm script 대신 Node.js 파일을 직접 실행할 수도 있다.

```sh
node news_array_scenarios/scenario07_keyword.js --query "삼성전자 실적" --limit 5
```

직접 실행에서도 MQL 출력, 수행시간 출력, 로그 기록 방식은 동일하다.

## 결과 저장

조회 결과 JSON만 파일로 저장한다.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --limit 100 > scenario3_result.json
```

MQL과 수행시간까지 함께 파일로 저장하려면 stderr도 redirect한다.

```sh
npm run scenario:3 -- --shcode 005930 --query "삼성전자 실적" --limit 100 > scenario3_result.json 2> scenario3_log.txt
```

## 참고

검색어가 있는 시나리오는 `title`, `contents`를 대상으로 검색한다.

검색어가 있는 일반 시나리오는 `score` 1차, `newscode_ts` 2차로 정렬한다.

검색어가 없는 조건 조회 시나리오는 `newscode_ts` 최신순으로 정렬한다.

시나리오 1은 현재 POC 확인용으로 기본 검색어 `에헤라`를 사용한다.
