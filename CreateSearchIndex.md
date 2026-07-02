# Atlas Search Index 생성 가이드

이 문서는 `news_array` 컬렉션에 Atlas Search 인덱스를 생성하고 테스트하는 방법을 정리한다.

## 전제

로딩 대상 컬렉션:

```text
Database: newsdb
Collection: news_array
```

테스트 데이터 파일:

```text
kbpoc/generated_news_collection_1gb/news_unified_collection_1gb_contents_array.json
```

문서 구조:

```js
{
  _id: ObjectId(...),
  newscode_ts: ISODate(...),
  title: "...",
  contents: ["...", "...", "..."],
  dgubun: "P",
  shcode: ["005930", "000660"],
  kind: ["P3", "030000"]
}
```

주의할 필드명:

| 필드 | 설명 |
|---|---|
| `contents` | 본문 배열 필드. `content`가 아님 |
| `kind` | 소문자 필드. `Kind`가 아님 |
| `news_array` | 현재 테스트 대상 컬렉션명 |

## 데이터 로딩

`mongoimport`는 `mongosh` 내부가 아니라 OS 터미널에서 실행한다.

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --db newsdb \
  --collection news_array \
  --drop \
  --file "/Users/sumi.ryu/Documents/opencode/kbpoc/generated_news_collection_1gb/news_unified_collection_1gb_contents_array.json"
```

`MONGODB_URI`에 이미 `/newsdb`가 포함되어 있으면 `--db newsdb`는 생략할 수 있다.

## mongosh 접속

터미널에서 접속한다.

```sh
mongosh "$MONGODB_URI"
```

DB를 선택한다.

```js
use newsdb
```

로딩 건수를 확인한다.

```js
db.news_array.countDocuments()
```

예상 건수:

```text
1494527
```

샘플 문서를 확인한다.

```js
db.news_array.findOne()
```

## Search Index 생성

`news_array` 컬렉션에 `news_search_index`를 생성한다.

```js
db.runCommand({
  createSearchIndexes: "news_array",
  indexes: [
    {
      name: "news_search_index",
      definition: {
        mappings: {
          dynamic: false,
          fields: {
            title: {
              type: "string",
              analyzer: "lucene.nori",
              searchAnalyzer: "lucene.nori"
            },
            contents: {
              type: "string",
              analyzer: "lucene.nori",
              searchAnalyzer: "lucene.nori"
            },
            shcode: {
              type: "token"
            },
            dgubun: {
              type: "token"
            },
            kind: {
              type: "token"
            },
            newscode_ts: {
              type: "date"
            }
          }
        }
      }
    }
  ]
})
```

## 필드 타입 선택 이유

| 필드 | 타입 | 이유 |
|---|---|---|
| `title` | `string` + `lucene.nori` | 한국어 뉴스 제목 형태소 검색 |
| `contents` | `string` + `lucene.nori` | 한국어 뉴스 본문 검색 |
| `shcode` | `token` | 종목코드 exact filter 검색 |
| `dgubun` | `token` | 뉴스구분 exact filter 검색 |
| `kind` | `token` | kind 값 exact filter 검색 |
| `newscode_ts` | `date` | 최신순 정렬 및 날짜 조건 |

`contents`, `shcode`, `kind`는 배열 필드다. Atlas Search는 문자열 배열도 인덱싱할 수 있으므로 위 매핑으로 사용할 수 있다.

## 인덱스 상태 확인

전체 Search Index 목록 확인:

```js
db.news_array.aggregate([
  { $listSearchIndexes: {} }
])
```

특정 인덱스 확인:

```js
db.news_array.aggregate([
  { $listSearchIndexes: { name: "news_search_index" } }
])
```

상태가 `READY`가 되면 검색 가능하다. 1GB 데이터이므로 인덱스 생성에는 시간이 걸릴 수 있다.

## 검색 테스트

### 1. 제목/본문 검색

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      text: {
        query: "삼성전자",
        path: ["title", "contents"]
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
      shcode: 1,
      kind: 1
    }
  }
])
```
```
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      phrase: {
        query: "삼성전자",
        path: ["title", "contents"]
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
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
])
```
### 2. 검색어 + 종목코드 filter

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "반도체",
              path: ["title", "contents"]
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode",
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
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
])
```

### 3. 검색어 없는 전체 조회

검색어가 없어도 Search를 사용해야 하는 경우 `exists` filter를 사용한다.

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        filter: [
          {
            exists: {
              path: "newscode_ts"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 100 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
    }
  }
])
```

### 4. 검색어 없는 뉴스구분 filter

```js
db.news_array.aggregate([
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
  { $limit: 100 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
    }
  }
])
```

### 5. 검색어 없는 종목코드 filter

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "shcode",
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
  { $limit: 100 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
    }
  }
])
```

## 자주 틀리는 부분

컬렉션명을 잘못 지정하면 인덱스가 다른 컬렉션에 만들어진다.

```text
현재 컬렉션명: news_array
```

본문 필드명을 `content`로 만들면 검색되지 않는다.

```text
현재 본문 필드명: contents
```

`kind`는 소문자다.

```text
현재 필드명: kind
```

`mongoimport` 명령은 `mongosh` 안에서 실행하지 않는다. OS 터미널에서 실행한다.

## 참고

Atlas UI에서도 Search Index를 생성할 수 있다.

```text
Atlas UI > Database > Browse Collections > newsdb.news_array > Search Indexes > Create Search Index
```

JSON Editor를 선택한 뒤 위 index definition의 `definition` 내부 내용을 입력하면 된다.
