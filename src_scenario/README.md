# news_mig Title-Only MQL 시나리오

`news_mig` 컬렉션과 `news_search_index` 기준으로 실행하는 시나리오별 MQL을 정리한다.

## 기준

```text
Database: newsdb
Collection: news_mig
Search Index: news_search_index
```

시나리오 프로그램 위치:

```text
kbpoc/news_mig_scenarios/
```

npm script:

```text
mig:1
mig:2
mig:3
mig:4
mig:5
mig:6
mig:7
mig:8
mig:9
mig:10
mig:11
```

## Search Index 기준

`news_mig`에는 아래 이름의 Atlas Search Index가 있다고 가정한다.

```text
news_search_index
```

필드 구조는 다음 기준이다.

| 필드 | 타입 | 용도 |
|---|---|---|
| `title` | `string`, `lucene.nori` | 제목 검색 |
| `contents` | `string`, `lucene.nori` | 본문 검색, 9/10번 기능 검증용 |
| `shcode.shcode` | `token` | 종목코드 exact filter |
| `dgubun` | `token` | 뉴스구분 exact filter |
| `newscode_ts` | `number` | 최신순 정렬 |

## 변경 기준

기존 `news_mig_500` 기준을 아래처럼 변경했다.

| 항목 | 변경 전 | 변경 후 |
|---|---|---|
| Collection | `news_mig_500` | `news_mig` |
| Search Index | `news5_search_index` | `news_search_index` |
| npm script prefix | `mig500:*` | `mig:*` |

1~8번 시나리오의 일반 검색은 `title`만 조회하도록 구성했다.

```js
text: {
  query: "삼성전자",
  path: "title",
  matchCriteria: "all"
}
```

9번 fuzzy와 10번 highlight는 기능 검증 목적상 `title`, `contents`를 모두 사용한다.

## 실행 방법

아래 명령은 `kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

MQL만 확인하려면 `--dry-run`을 사용한다.

```sh
npm run mig:4 -- --dgubun 4 --query "삼성전자" --limit 5 --dry-run
```

실제 실행은 `--dry-run`을 제거한다.

```sh
npm run mig:4 -- --dgubun 4 --query "삼성전자" --limit 5
```

## 공통 옵션

| 옵션 | 설명 | 기본값 |
|---|---|---|
| `--uri` | MongoDB 접속 문자열 | `MONGODB_URI` 환경변수 |
| `--db` | database 이름 | `newsdb` |
| `--collection` | collection 이름 | `news_mig` |
| `--index` | Atlas Search index 이름 | `news_search_index` |
| `--shcode-path` | 종목코드 filter path | `shcode.shcode` |
| `--limit` | 조회 건수 | `100` |
| `--dry-run` | MongoDB 접속 없이 MQL만 출력 | 비활성 |
| `--no-log` | 로그 파일 기록 비활성화 | 비활성 |

## 시나리오 1

조건:

```text
검색어 있음
종목코드 없음
뉴스구분 없음
title 검색 후 최신순 조회
```

실행:

```sh
npm run mig:1 -- --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 2

조건:

```text
뉴스구분 있음
종목코드 없음
검색어 없음
뉴스구분 조건 조회
```

실행:

```sh
npm run mig:2 -- --dgubun P --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "P"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 3

조건:

```text
종목코드 있음
검색어 있음
뉴스구분 없음
종목코드 filter + title 검색
```

실행:

```sh
npm run mig:3 -- --shcode 005930 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 4

조건:

```text
종목코드 없음
뉴스구분 있음
검색어 있음
뉴스구분 filter + title 검색
```

실행:

```sh
npm run mig:4 -- --dgubun 4 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "4"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 5

조건:

```text
종목코드 있음
뉴스구분 없음
검색어 없음
종목코드 조건 조회
```

실행:

```sh
npm run mig:5 -- --shcode 005930 --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 6

조건:

```text
종목코드 있음
뉴스구분 있음
검색어 없음
종목코드 + 뉴스구분 조건 조회
```

실행:

```sh
npm run mig:6 -- --shcode 005930 --dgubun P --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          },
          {
            equals: {
              path: "dgubun",
              value: "P"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 7

조건:

```text
검색어 있음
종목코드 없음
뉴스구분 없음
title 전체 검색
```

실행:

```sh
npm run mig:7 -- --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 8

조건:

```text
뉴스구분 있음
검색어 있음
종목코드 없음
뉴스구분 filter + title 검색
```

실행:

```sh
npm run mig:8 -- --dgubun 4 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "4"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 9

9번은 fuzzy 기능 검증 목적이므로 `title`, `contents` should 검색을 유지한다.

실행:

```sh
npm run mig:9 -- --query "삼영전자" --limit 5
```

## 시나리오 10

10번은 highlight 기능 검증 목적이므로 `title`, `contents` 검색과 highlight path를 유지한다.

실행:

```sh
npm run mig:10 -- --query "삼성전자 실적" --limit 5
```

## 검증 완료

아래 dry-run으로 `db.news_mig`와 `news_search_index` 사용을 확인했다.

```sh
npm run mig:1 -- --query "삼성전자" --dry-run --limit 1 --no-log
npm run mig:4 -- --dgubun 4 --query "삼성전자" --dry-run --limit 1 --no-log
npm run mig:10 -- --query "삼성전자 실적" --dry-run --limit 1 --no-log
```

대표 출력:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 1 }
]);
```
### 시나리오 11 쿼리 의미

`path: ["title", "contents"]`는 `title`과 `contents`가 둘 다 존재해야 한다는 의미가 아니다.

| 결과 유형 | 포함 필드 |
|---|---|
| title 문서 | `title`, `dgubun`, `shcode`, `newscode_ts` |
| contents 문서 | `parent`, `contents` |


## 검증 완료

아래 dry-run으로 `db.news_mig`와 `news_search_index` 사용을 확인

```sh
npm run mig:1 -- --query "삼성전자" --dry-run --limit 1 --no-log
npm run mig:4 -- --dgubun 4 --query "삼성전자" --dry-run --limit 1 --no-log
npm run mig:10 -- --query "삼성전자 실적" --dry-run --limit 1 --no-log
npm run mig:11 -- --query "삼성전자 실적" --dry-run --limit 1 --no-log
```

대표 출력:

```js
db.news_mig.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 1 }
]);
```
## 참고

`news_mig`이 split document 구조라면 `title/shcode` 문서와 `contents` 문서가 분리되어 있을 수 있다.

1~8번 업무 검색은 parent document의 `title` 중심으로 수행한다.

본문까지 결과에 붙여야 하는 경우에는 parent `_id` 기준으로 contents document를 `$lookup`하는 별도 쿼리가 필요하다.
