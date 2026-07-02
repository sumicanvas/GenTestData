# news_array 컬렉션 MQL 시나리오

`260701_MongoDB_PoC 검증 시나리오_교보증권.xlsx`의 시나리오를 `news_array` 컬렉션 기준으로 재작성한 MQL이다.

## 전제

대상 컬렉션:

```text
Database: newsdb
Collection: news_array
Search Index: news_search_index
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

공통 기준:

| 항목 | 기준 |
|---|---|
| 컬렉션 | `news_array` |
| 검색 인덱스 | `news_search_index` |
| 본문 필드 | `contents` |
| kind 필드 | `kind` |
| 날짜 정렬 필드 | `newscode_ts` |
| 검색어 있는 경우 | `score` 1차, `newscode_ts` 2차 정렬 |
| 검색어 없는 경우 | `newscode_ts` 최신순 정렬 |

검색어가 있는 시나리오는 `text` 검색을 사용하고 `matchCriteria: "all"`을 적용한다.

```js
sort: {
  score: { $meta: "searchScore" },
  newscode_ts: -1
}
```

## 시나리오 1

조건:

```text
종목코드 없음
뉴스구분 없음
검색어 없음
전체 뉴스 최신순 조회
```

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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
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
해당 뉴스매체 전체 뉴스 최신순 조회
```

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
              value: "<뉴스구분>"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
    }
  }
]);
```

## 시나리오 3

조건:

```text
뉴스구분 없음
종목코드 있음
검색어 있음
해당 종목의 검색 결과 조회
```

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "<검색어>",
              path: ["title", "contents"],
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode",
              value: "<종목코드>"
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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 4

조건:

```text
뉴스구분 있음
종목코드 있음
검색어 있음
해당 종목 + 해당 뉴스매체의 검색 결과 조회
```

참고: 엑셀 설명에는 종목코드 없음으로 적힌 부분이 있으나, Oracle 조건에는 종목코드 조건이 포함되어 있어 종목코드 조건을 반영했다.

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성생명",
              path: ["title", "contents"],
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "S"
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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
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
해당 종목의 전체 뉴스 최신순 조회
```

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
              value: "000660"
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
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
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
해당 종목 + 해당 뉴스매체의 전체 뉴스 최신순 조회
```

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
              value: "000660"
            }
          },
          {
            equals: {
              path: "dgubun",
              value: "4"
            }
          }
        ]
      },
      sort: {
        newscode_ts: -1
      }
    }
  },
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1
    }
  }
]);
```

## 시나리오 7

조건:

```text
종목코드 없음
뉴스구분 없음
검색어 있음
전체 뉴스 검색 결과 조회
```

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: ["title", "contents"],
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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 8

조건:

```text
종목코드 없음
뉴스구분 있음
검색어 있음
해당 뉴스매체의 검색 결과 조회
```

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "해운업종",
              path: ["title", "contents"],
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "M"
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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 9

조건:

```text
Fuzzy 검색
오타가 있어도 유사 결과가 조회되는지 확인
```

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼영전자",
              path: "title",
              matchCriteria: "all",
              fuzzy: {
                maxEdits: 1,
                prefixLength: 1,
                maxExpansions: 50
              }
            }
          }
        ],
        should: [
          {
            text: {
              query: "삼영전자",
              path: "contents",
              matchCriteria: "all",
              fuzzy: {
                maxEdits: 1,
                prefixLength: 1,
                maxExpansions: 50
              }
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
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 10

조건:

```text
Highlight 기능
검색어가 매칭된 title 또는 contents 일부를 highlight로 반환
```

```js
db.news_array.aggregate([
  {
    $search: {
      index: "news_search_index",
      compound: {
        must: [
          {
            text: {
              query: "<검색어>",
              path: ["title", "contents"],
              matchCriteria: "all"
            }
          }
        ]
      },
      highlight: {
        path: ["title", "contents"]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  { $limit: 10 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      kind: 1,
      score: { $meta: "searchScore" },
      highlights: { $meta: "searchHighlights" }
    }
  }
]);
```

## 치환 값 예시

```text
<검색어>   -> 삼성전자 실적
<뉴스구분> -> P
<종목코드> -> 005930
```

## 참고 사항

검색어가 없는 시나리오에서는 검색 점수의 의미가 거의 없으므로 `score`를 출력하지 않는다.

검색어가 있는 시나리오는 `text` 검색을 사용한다. `lucene.nori` 분석기 특성상 `삼성전자` 같은 검색어가 토큰화될 수 있으므로, POC에서는 `matchCriteria: "all"`을 사용해 검색어 토큰을 모두 포함하는 결과를 우선한다.

정확한 구문 일치가 필요하면 `text` 대신 `phrase`를 검토할 수 있지만, `삼성전자 실적`처럼 확장 검색이 필요한 POC에서는 `text` 방식이 더 적합하다.
