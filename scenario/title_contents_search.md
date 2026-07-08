# news_mig_500 제목/본문 Split 구조 검색 MQL

`news_mig_500` 컬렉션은 제목/종목코드 문서와 본문 문서가 분리된 구조다.

```text
parent document : title, dgubun, shcode, newscode_ts
child document  : parent, contents
```

예시는 다음과 같다.

```js
{
  _id: ObjectId("69553a70272d62b39e0bdd46"),
  dgubun: "4",
  title: "삼성전자, 반도체 업황 회복 기대에 강세",
  newscode_ts: 1767193200000,
  shcode: [
    {
      shcode: "005930",
      expcode: "A005930"
    }
  ]
}
```

```js
{
  _id: ObjectId("69553a70272d62b39f0bdd46"),
  parent: ObjectId("69553a70272d62b39e0bdd46"),
  contents: [
    "<div class=\"news\"><p><strong>삼성전자</strong>...",
    "증권가는 외국인 수급과 분기 실적 전망을...",
    "테스트 기사</td></tr></table></div>"
  ]
}
```

## 사용하는 Search Index

현재 사용하는 Search Index는 다음이다.

```text
Collection: news_mig_500
Search Index: news5_search_index
```

Index mapping 기준:

```js
{
  title: "string",
  contents: "string",
  shcode: {
    type: "document",
    fields: {
      shcode: "token"
    }
  },
  dgubun: "token",
  newscode_ts: "number"
}
```

## 기존 쿼리가 실패하는 이유

아래처럼 `$search` 안에서 `shcode.shcode` filter를 걸면 title 문서는 검색되지만 contents 문서는 제외된다.

```js
filter: [
  {
    equals: {
      path: "shcode.shcode",
      value: "005930"
    }
  }
]
```

contents 문서에는 `shcode`가 없기 때문이다.

따라서 `title`과 `contents`를 모두 검색하려면 다음 순서가 필요하다.

```text
1. $search에서 title/contents 전체 검색
2. 검색 결과가 child contents 문서이면 parent id를 가져옴
3. parent 문서를 lookup
4. parent 문서의 shcode/dgubun 조건을 일반 $match로 적용
5. child contents 문서를 lookup해 결과에 붙임
6. 같은 parent 기준으로 중복 제거
```

## 권장 MQL: 제목/본문 모두 검색 + 종목코드 조건

아래 쿼리는 `title` 또는 `contents`에서 `삼성전자 실적`을 검색하고, parent 문서의 `shcode.shcode = 005930` 조건을 적용한다.

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
        ]
      }
    }
  },
  {
    $addFields: {
      score: { $meta: "searchScore" },
      parent_id: {
        $ifNull: ["$parent", "$_id"]
      },
      matched_doc_type: {
        $cond: [
          { $ne: ["$parent", null] },
          "contents",
          "title"
        ]
      }
    }
  },
  {
    $lookup: {
      from: "news_mig_500",
      localField: "parent_id",
      foreignField: "_id",
      as: "parent_doc"
    }
  },
  {
    $set: {
      parent_doc: {
        $arrayElemAt: ["$parent_doc", 0]
      }
    }
  },
  {
    $match: {
      "parent_doc.shcode.shcode": "005930"
    }
  },
  {
    $lookup: {
      from: "news_mig_500",
      localField: "parent_doc._id",
      foreignField: "parent",
      as: "content_doc"
    }
  },
  {
    $set: {
      content_doc: {
        $arrayElemAt: ["$content_doc", 0]
      }
    }
  },
  {
    $group: {
      _id: "$parent_doc._id",
      score: { $max: "$score" },
      matched_doc_types: { $addToSet: "$matched_doc_type" },
      newscode_ts: { $first: "$parent_doc.newscode_ts" },
      title: { $first: "$parent_doc.title" },
      dgubun: { $first: "$parent_doc.dgubun" },
      shcode: { $first: "$parent_doc.shcode" },
      kind: { $first: "$parent_doc.kind" },
      contents: { $first: "$content_doc.contents" }
    }
  },
  {
    $sort: {
      score: -1,
      newscode_ts: -1
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
      kind: 1,
      matched_doc_types: 1,
      score: 1
    }
  }
]);
```

## 뉴스구분 조건까지 추가한 MQL

뉴스구분까지 함께 적용하려면 `$match`에 `parent_doc.dgubun` 조건을 추가한다.

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
        ]
      }
    }
  },
  {
    $addFields: {
      score: { $meta: "searchScore" },
      parent_id: {
        $ifNull: ["$parent", "$_id"]
      },
      matched_doc_type: {
        $cond: [
          { $ne: ["$parent", null] },
          "contents",
          "title"
        ]
      }
    }
  },
  {
    $lookup: {
      from: "news_mig_500",
      localField: "parent_id",
      foreignField: "_id",
      as: "parent_doc"
    }
  },
  {
    $set: {
      parent_doc: {
        $arrayElemAt: ["$parent_doc", 0]
      }
    }
  },
  {
    $match: {
      "parent_doc.shcode.shcode": "005930",
      "parent_doc.dgubun": "4"
    }
  },
  {
    $lookup: {
      from: "news_mig_500",
      localField: "parent_doc._id",
      foreignField: "parent",
      as: "content_doc"
    }
  },
  {
    $set: {
      content_doc: {
        $arrayElemAt: ["$content_doc", 0]
      }
    }
  },
  {
    $group: {
      _id: "$parent_doc._id",
      score: { $max: "$score" },
      matched_doc_types: { $addToSet: "$matched_doc_type" },
      newscode_ts: { $first: "$parent_doc.newscode_ts" },
      title: { $first: "$parent_doc.title" },
      dgubun: { $first: "$parent_doc.dgubun" },
      shcode: { $first: "$parent_doc.shcode" },
      kind: { $first: "$parent_doc.kind" },
      contents: { $first: "$content_doc.contents" }
    }
  },
  {
    $sort: {
      score: -1,
      newscode_ts: -1
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
      kind: 1,
      matched_doc_types: 1,
      score: 1
    }
  }
]);
```

## 단계별 설명

### 1. `$search`

`title`과 `contents`를 모두 검색한다.

```js
text: {
  query: "삼성전자 실적",
  path: ["title", "contents"],
  matchCriteria: "all"
}
```

이 단계에서는 `shcode` filter를 걸지 않는다.

contents 문서에는 `shcode`가 없기 때문이다.

### 2. `parent_id` 계산

검색 결과가 child contents 문서이면 `parent` 값을 사용한다.

검색 결과가 parent title 문서이면 자기 자신의 `_id`를 사용한다.

```js
parent_id: {
  $ifNull: ["$parent", "$_id"]
}
```

### 3. parent 문서 lookup

`parent_id`로 parent document를 찾는다.

```js
$lookup: {
  from: "news_mig_500",
  localField: "parent_id",
  foreignField: "_id",
  as: "parent_doc"
}
```

### 4. parent 기준 필터 적용

종목코드와 뉴스구분은 parent document에 있으므로 lookup 이후 `$match`로 적용한다.

```js
$match: {
  "parent_doc.shcode.shcode": "005930",
  "parent_doc.dgubun": "4"
}
```

### 5. contents 문서 lookup

최종 결과에 본문을 붙이기 위해 parent `_id`로 child contents 문서를 찾는다.

```js
$lookup: {
  from: "news_mig_500",
  localField: "parent_doc._id",
  foreignField: "parent",
  as: "content_doc"
}
```

### 6. parent 기준 중복 제거

title 문서와 contents 문서가 모두 검색될 수 있으므로 parent `_id` 기준으로 group 한다.

```js
$group: {
  _id: "$parent_doc._id",
  score: { $max: "$score" },
  ...
}
```

## 주의사항

이 방식은 `$search`에서 먼저 전체 title/contents 검색을 수행한 뒤 parent 조건을 적용한다.

따라서 검색 대상이 아주 크고 조건이 선택적이면 unified document 구조보다 비효율적일 수 있다.

검색 성능과 정확도를 모두 중요하게 보면 `title`, `shcode`, `contents`가 한 document에 들어간 unified target이 더 적합하다.

## 권장 판단

| 목적 | 권장 방식 |
|---|---|
| 현재 split 구조 그대로 검색 | 이 문서의 `$search + parent lookup` MQL 사용 |
| 종목코드 기준 title만 검색 | `path: "title"` + `shcode.shcode` filter 사용 |
| title/contents를 동시에 정확하게 검색 | unified migration target 사용 |
| 높은 검색 성능 | unified migration target 사용 |
