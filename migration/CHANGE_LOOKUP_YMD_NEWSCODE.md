# `$unionWith` 기반 content lookup 제안 검토

`migration_mg`에서 `news_mast`와 `news_cont_*`를 merge할 때, 고객이 전달한 `$unionWith` 기반 lookup 제안을 검토한 내용이다.

## 고객 요구사항

뉴스 본문을 찾을 때 아래 순서로 조회한다.

```text
1순위: YMD + NEWSCODE
2순위: YMD + SEQNO
```

즉 `YMD + NEWSCODE`로 먼저 찾고, 없으면 `YMD + SEQNO`로 fallback 한다.

## 현재 migration_mg 구조

`migration_mg`는 `news_mast`에서 batch 문서를 읽은 뒤, 해당 batch를 `$documents`로 aggregation에 넘긴다.

파일:

```text
kbpoc/migration_mg/cont.js
```

현재 구조:

```js
export async function migrate_conts(db, docs) {
  const promises = CO_CONT_LIST.map(async (co_cont) => {
    let pipeline_migrate = [
      { $documents: docs },
      ...pipeline.newsid2contid,
      ...pipeline.migrate_cont,
    ];

    pipeline_migrate.at(-3)["$lookup"].from = co_cont;
    return await db
      .aggregate(pipeline_migrate, { allowDiskUse: true })
      .toArray();
  });
  await Promise.all(promises);
}
```

즉 source가 실제 collection이 아니라 메모리상의 `docs`이다.

```text
source = { $documents: docs }
```

## 고객이 제안한 `$unionWith` 방식

고객 제안은 대략 다음 구조다.

```js
db.source_collection.aggregate([
  ...pipeline.fetch_transform_tmp,

  // Branch 1: YMD + SEQNO
  {
    $lookup: {
      from: "news_cont_p",
      let: { ymd: "$ymd", seq: "$seqno" },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$YMD", "$$ymd"] },
                { $eq: ["$SEQNO", "$$seq"] }
              ]
            }
          }
        },
        { $sort: { LINENO: 1 } },
        {
          $group: {
            _id: "$YMD",
            contents: { $push: "$CONTENT" }
          }
        }
      ],
      as: "lookupContents"
    }
  },
  { $match: { "lookupContents.0": { $exists: true } } },
  {
    $set: {
      seqno: "$$REMOVE",
      contents: { $arrayElemAt: ["$lookupContents.contents", 0] }
    }
  },
  { $unset: "lookupContents" },

  // Branch 2: YMD + NEWSCODE
  {
    $unionWith: {
      coll: "source_collection",
      pipeline: [
        ...pipeline.fetch_transform_tmp,
        {
          $lookup: {
            from: "news_cont_p",
            let: { ymd: "$ymd", newscode: "$newscode" },
            pipeline: [
              {
                $match: {
                  $expr: {
                    $and: [
                      { $eq: ["$YMD", "$$ymd"] },
                      { $eq: ["$NEWSCODE", "$$newscode"] }
                    ]
                  }
                }
              },
              { $sort: { LINENO: 1 } },
              {
                $group: {
                  _id: "$YMD",
                  contents: { $push: "$CONTENT" }
                }
              }
            ],
            as: "lookupContents"
          }
        },
        { $match: { "lookupContents.0": { $exists: true } } },
        {
          $set: {
            seqno: "$$REMOVE",
            contents: { $arrayElemAt: ["$lookupContents.contents", 0] }
          }
        },
        { $unset: "lookupContents" }
      ]
    }
  },

  ...pipeline.newsid2contid,
  {
    $merge: {
      into: process.env.CO_TO,
      on: "_id",
      whenMatched: "keepExisting",
      whenNotMatched: "insert"
    }
  }
]);
```

## 제안 방식의 장점

`YMD + SEQNO`와 `YMD + NEWSCODE`를 독립 branch로 나누기 때문에, 각 lookup 전략의 결과를 명확히 분리할 수 있다.

결과가 없는 branch는 아래 조건으로 제거한다.

```js
{ $match: { "lookupContents.0": { $exists: true } } }
```

즉 content가 실제로 붙은 문서만 다음 단계로 전달된다.

## 바로 적용하기 어려운 이유

### 1. 현재 migration_mg는 실제 source collection을 쓰지 않음

`$unionWith`는 실제 collection 이름을 필요로 한다.

```js
$unionWith: {
  coll: "source_collection"
}
```

하지만 현재 `migration_mg`는 source가 collection이 아니라 아래처럼 `$documents`이다.

```js
{ $documents: docs }
```

따라서 고객이 제안한 `$unionWith` 방식을 그대로 쓰려면 batch 문서를 먼저 임시 collection에 저장해야 한다.

예:

```text
transform_tmp_1
transform_tmp_2
...
```

그 다음에야 아래가 가능하다.

```js
db.transform_tmp_1.aggregate([
  ...branch1,
  {
    $unionWith: {
      coll: "transform_tmp_1",
      pipeline: [...branch2]
    }
  }
])
```

### 2. 우선순위가 고객 요구와 반대일 수 있음

고객 요구사항은 다음이다.

```text
1순위: YMD + NEWSCODE
2순위: YMD + SEQNO
```

하지만 전달받은 예시에서는 Branch 1이 `YMD + SEQNO`이고 Branch 2가 `YMD + NEWSCODE`이다.

```text
Branch 1: YMD + SEQNO
Branch 2: YMD + NEWSCODE
```

이 상태에서 `$merge`가 아래처럼 되어 있으면:

```js
whenMatched: "keepExisting"
```

먼저 들어간 `YMD + SEQNO` 결과가 유지되고, 나중의 `YMD + NEWSCODE` 결과가 무시될 수 있다.

즉 우선순위가 반대로 적용될 위험이 있다.

## 현재 migration_mg에 더 적합한 권장 방식

현재 구조를 크게 바꾸지 않으려면 `$unionWith`보다 단일 `$lookup` 안에서 priority를 주는 방식이 더 적합하다.

로직은 다음과 같다.

```text
YMD는 반드시 일치
그리고
NEWSCODE 일치 또는 SEQNO 일치
```

그 다음 priority를 부여한다.

```text
_matchPriority = 1  // YMD + NEWSCODE 매칭
_matchPriority = 2  // YMD + SEQNO fallback 매칭
```

정렬:

```js
$sort: {
  _matchPriority: 1,
  LINENO: 1
}
```

이렇게 하면 `YMD + NEWSCODE` 결과가 있으면 먼저 선택되고, 없을 때 `YMD + SEQNO` 결과가 선택된다.

## 권장 변경 위치

파일:

```text
kbpoc/migration_mg/pipeline.js
```

변경 대상:

```text
transform_tmp
newsid2contid
migrate_cont
```

### transform_tmp에 ymd, newscode 추가

```js
transform_tmp: [
  {
    $project: {
      _id: "$_newsId",
      dgubun: "$DGUBUN",
      ymd: "$YMD",
      title: "$TITLE",
      seqno: "$SEQNO",
      newscode: "$NEWSCODE",
      newscode_ts: { $toLong: "$_date" },
      kind: ["$KIND", "$KIND2"],
      shcodeTop: "$SHCODE",
    },
  },
]
```

### newsid2contid에 ymd, newscode 전달

```js
newsid2contid: [
  {
    $project: {
      _id: 0,
      ymd: 1,
      seqno: 1,
      newscode: 1,
      parent: "$_id",
      oidrand: {
        ...
      }
    }
  },
  ...
]
```

### migrate_cont에서 priority lookup 적용

```js
migrate_cont: [
  {
    $lookup: {
      from: process.env.CO_CONT_LIST?.split(",")[0]?.trim() || "news_cont_p",
      let: {
        ymd: "$ymd",
        seq: "$seqno",
        newscode: "$newscode",
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                {
                  $eq: ["$YMD", "$$ymd"]
                },
                {
                  $or: [
                    {
                      $eq: ["$NEWSCODE", "$$newscode"]
                    },
                    {
                      $eq: ["$SEQNO", "$$seq"]
                    }
                  ]
                }
              ]
            }
          }
        },
        {
          $addFields: {
            _matchPriority: {
              $cond: [
                {
                  $eq: [
                    "$NEWSCODE",
                    "$$newscode"
                  ]
                },
                1,
                2
              ]
            }
          }
        },
        {
          $sort: {
            _matchPriority: 1,
            LINENO: 1
          }
        },
        {
          $group: {
            _id: "$_matchPriority",
            contents: { $push: "$CONTENT" }
          }
        },
        {
          $sort: {
            _id: 1
          }
        },
        {
          $limit: 1
        }
      ],
      as: "contents"
    }
  },
  {
    $set: {
      ymd: "$$REMOVE",
      seqno: "$$REMOVE",
      newscode: "$$REMOVE",
      contents: {
        $arrayElemAt: ["$contents.contents", 0]
      }
    }
  },
  {
    $merge: {
      into: process.env.CO_TO,
      on: "_id",
      whenMatched: "keepExisting",
      whenNotMatched: "insert"
    }
  }
]
```

## SEQNO 타입 전제

고객 데이터에서 `YMD`, `SEQNO`, `NEWSCODE`가 모두 문자열로 들어오는 것이 확인되었다.

따라서 비교는 직접 문자열 비교로 수행한다.

```js
{ $eq: ["$SEQNO", "$$seq"] }
```

앞자리 0도 문자열 값으로 보존되므로 padding 처리는 하지 않는다.

## 권장 인덱스

`news_cont_*` 컬렉션마다 아래 인덱스를 권장한다.

```js
db.news_cont_p.createIndex({ YMD: 1, NEWSCODE: 1, LINENO: 1 })
db.news_cont_p.createIndex({ YMD: 1, SEQNO: 1, LINENO: 1 })
```

`news_cont_` 컬렉션이 여러 개면 각각 생성한다.

```js
db.news_cont_i.createIndex({ YMD: 1, NEWSCODE: 1, LINENO: 1 })
db.news_cont_i.createIndex({ YMD: 1, SEQNO: 1, LINENO: 1 })
```

## 검증 쿼리

### YMD + NEWSCODE 매칭 건수 확인

```js
db.news_mast.aggregate([
  {
    $lookup: {
      from: "news_cont_p",
      let: {
        ymd: "$YMD",
        newscode: "$NEWSCODE"
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$YMD", "$$ymd"] },
                { $eq: ["$NEWSCODE", "$$newscode"] }
              ]
            }
          }
        },
        { $limit: 1 }
      ],
      as: "cont"
    }
  },
  { $match: { cont: { $ne: [] } } },
  { $count: "matched_by_ymd_newscode" }
])
```

### YMD + SEQNO 매칭 건수 확인

```js
db.news_mast.aggregate([
  {
    $lookup: {
      from: "news_cont_p",
      let: {
        ymd: "$YMD",
        seq: "$SEQNO"
      },
      pipeline: [
        {
          $match: {
            $expr: {
              $and: [
                { $eq: ["$YMD", "$$ymd"] },
                { $eq: ["$SEQNO", "$$seq"] }
              ]
            }
          }
        },
        { $limit: 1 }
      ],
      as: "cont"
    }
  },
  { $match: { cont: { $ne: [] } } },
  { $count: "matched_by_ymd_seqno" }
])
```

## 결론

`$unionWith` 방식은 가능하지만 현재 `migration_mg` 구조에는 바로 적용하기 어렵다.

현재 구조에서는 priority 기반 단일 `$lookup` 방식이 수정 범위가 작고 안전하다.

권장 로직:

```text
1. YMD + NEWSCODE로 먼저 찾는다.
2. 없으면 YMD + SEQNO로 fallback 한다.
3. LINENO 오름차순으로 CONTENT 배열을 만든다.
```
