# news_mig_500 검색 결과 0건 원인과 해결 방안

`news_mig_500` 컬렉션에서 Atlas Search 쿼리 결과가 0건으로 나오는 원인과 해결 방법을 정리한다.

## 상황

아래 쿼리를 실행했을 때 결과가 나오지 않았다.

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자 실적",
              path: ["title", "contents"],
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

## 확인된 Search Index

`news_mig_500`에는 아래 Search Index가 생성되어 있다.

```text
Index Name: news5_search_index
Collection: news_mig_500
```

Index definition:

```js
db.runCommand({
  createSearchIndexes: "news_mig_500",
  indexes: [
    {
      name: "news5_search_index",
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
              type: "document",
              fields: {
                shcode: {
                  type: "token"
                }
              }
            },
            dgubun: {
              type: "token"
            },
            newscode_ts: {
              type: "number"
            }
          }
        }
      }
    }
  ]
});
```

Index는 `READY`, `queryable` 상태로 확인되었다.

## 원인

핵심 원인은 `news_mig_500`의 문서 구조다.

`news_mig_500`은 뉴스 1건이 하나의 document에 통합되어 있지 않고, 두 document로 나뉘어 있다.

### 1. title/shcode 문서

첫 번째 문서는 제목, 뉴스구분, 종목코드를 가진다.

```js
{
  _id: ObjectId("69553a705683d88cc08007b3"),
  dgubun: "4",
  title: "삼성전자, 반도체 업황 회복 기대에 강세",
  newscode_ts: 1767193200000,
  kind: ["01", "010000"],
  shcodeTop: "005930",
  shcode: [
    {
      shcode: "005930",
      expcode: "A005930"
    }
  ]
}
```

### 2. contents 문서

두 번째 문서는 본문을 가지고 있고, 원문 title document를 `parent`로 참조한다.

```js
{
  _id: ObjectId("69553a705683d88cc18007b3"),
  parent: ObjectId("69553a705683d88cc08007b3"),
  contents: [
    "<div class=\"news\"><p><strong>삼성전자</strong>(005930)은 반도체 업황 개선 기대에 장중 강세를 보였다.</p><p>",
    "증권가는 외국인 수급과 분기 실적 전망을 함께 확인해야 한다고 분석했다.</p><table><tr><td>인포스탁 ",
    "테스트 기사</td></tr></table></div>"
  ]
}
```

즉 실제 구조는 다음과 같다.

```text
title, dgubun, shcode -> parent document
contents              -> child document
```

## 왜 기존 쿼리가 0건인가

기존 쿼리는 아래 조건을 같은 document에서 모두 만족해야 한다.

```text
1. title 또는 contents에 "삼성전자 실적"의 모든 토큰이 있음
2. shcode.shcode = "005930"
```

하지만 현재 데이터는 다음처럼 나뉘어 있다.

| document | title | contents | shcode |
|---|---|---|---|
| parent | 있음 | 없음 | 있음 |
| child | 없음 | 있음 | 없음 |

따라서 아래 쿼리는 실패한다.

```js
text: {
  query: "삼성전자 실적",
  path: ["title", "contents"],
  matchCriteria: "all"
},
filter: [
  {
    equals: {
      path: "shcode.shcode",
      value: "005930"
    }
  }
]
```

`contents` 문서에는 `삼성전자`, `실적`이 있지만 `shcode`가 없다.

`title` 문서에는 `shcode`와 `삼성전자`가 있지만 `contents`가 없고, title에 `실적`이 없을 수 있다.

그래서 `matchCriteria: "all"` 조건이 깨진다.

## 확인 결과

일반 조회 기준 데이터는 존재한다.

```js
db.news_mig_500.countDocuments({ title: /삼성전자/ })
db.news_mig_500.countDocuments({ "shcode.shcode": "005930" })
db.news_mig_500.countDocuments({ contents: /실적/ })
```

실제 확인된 형태:

```text
"삼성전자" + shcode.shcode=005930 -> 결과 있음
"실적" + shcode.shcode=005930 -> 결과 있음
"삼성전자 실적" + shcode.shcode=005930 + matchCriteria all -> 결과 없음
"삼성전자 실적" + filter 없음 -> contents 문서에서 결과 있음
```

## 해결 방안 1. 현재 구조 유지, title 기준으로 검색

현재 `news_mig_500` 구조를 유지한다면 종목코드 filter가 필요한 검색은 parent document 기준으로 검색해야 한다.

즉 `title`만 검색 대상으로 둔다.

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title"
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
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

이 방식은 title과 shcode가 같은 document에 있기 때문에 정상 동작한다.

## 해결 방안 2. title 검색 후 contents를 lookup으로 붙이기

조회 결과에 본문까지 보여주고 싶다면, parent document를 먼저 검색한 뒤 child contents document를 `$lookup`으로 붙인다.

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title"
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
    $lookup: {
      from: "news_mig_500",
      localField: "_id",
      foreignField: "parent",
      as: "content_doc"
    }
  },
  {
    $set: {
      contents: {
        $arrayElemAt: ["$content_doc.contents", 0]
      }
    }
  },
  {
    $project: {
      content_doc: 0
    }
  }
]);
```

이 방식의 흐름은 다음과 같다.

```text
1. title/shcode가 있는 parent document를 Atlas Search로 검색
2. parent _id를 기준으로 child contents document를 lookup
3. 결과에 contents 배열을 붙여 반환
```

## 해결 방안 3. matchCriteria all 제거

`"삼성전자 실적"`을 꼭 하나의 검색어로 사용해야 한다면 `matchCriteria: "all"`을 제거할 수 있다.

```js
text: {
  query: "삼성전자 실적",
  path: "title"
}
```

예시:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자 실적",
              path: "title"
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
  { $limit: 5 }
]);
```

다만 이 방식은 `삼성전자` 또는 `실적` 중 일부 토큰만 맞아도 결과가 나올 수 있어 검색 정확도는 낮아질 수 있다.

## 해결 방안 4. Unified migration 컬렉션 사용

가장 근본적인 해결책은 `title`, `shcode`, `contents`가 같은 document에 들어간 target 컬렉션을 사용하는 것이다.

목표 구조:

```js
{
  _id: ObjectId("..."),
  title: "삼성전자, 반도체 업황 회복 기대에 강세",
  shcode: [
    {
      shcode: "005930",
      expcode: "A005930"
    }
  ],
  contents: [
    "...삼성전자...",
    "...실적..."
  ],
  dgubun: "4",
  newscode_ts: 1767193200000
}
```

이 구조에서는 원래 쿼리가 의도대로 동작한다.

```js
text: {
  query: "삼성전자 실적",
  path: ["title", "contents"],
  matchCriteria: "all"
},
filter: [
  {
    equals: {
      path: "shcode.shcode",
      value: "005930"
    }
  }
]
```

단, unified target 컬렉션에도 별도 Search Index를 생성해야 한다.

## 권장안

현재 `news_mig_500` 구조를 그대로 사용할 경우 권장 쿼리는 다음이다.

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title"
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
    $lookup: {
      from: "news_mig_500",
      localField: "_id",
      foreignField: "parent",
      as: "content_doc"
    }
  },
  {
    $set: {
      contents: {
        $arrayElemAt: ["$content_doc.contents", 0]
      }
    }
  },
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

이 쿼리는 parent 문서에서 검색과 종목코드 filter를 수행하고, child 문서의 contents를 결과에 붙인다.

## 정리

`news_mig_500`에서 결과가 0건인 이유는 index path 문제가 아니라 문서 분리 구조 때문이다.

```text
title/shcode와 contents가 서로 다른 document에 있음
```

현재 구조에서는 `shcode` filter가 필요한 검색은 parent document 기준으로 하고, 본문은 `$lookup`으로 붙이는 방식이 적합하다.

원래처럼 `title`, `shcode`, `contents`를 동시에 검색하려면 unified migration 결과 컬렉션을 사용해야 한다.
