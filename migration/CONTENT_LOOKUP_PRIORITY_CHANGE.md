# migration_mg content lookup 변경 사항

고객 요구사항에 맞춰 `news_mast`와 `news_cont_*`를 연결하는 기준을 수정했다.

## 고객 요구사항

본문을 찾을 때 아래 순서를 적용한다.

```text
1순위: YMD + NEWSCODE
2순위: YMD + SEQNO
```

즉 같은 `YMD` 안에서 `NEWSCODE`가 맞는 본문을 먼저 사용하고, 없으면 `SEQNO`가 맞는 본문을 fallback으로 사용한다.

## 수정 파일

```text
kbpoc/migration_mg/pipeline.js
```

## 변경 1. transform_tmp에 lookup key 보존

### 기존

```js
transform_tmp: [
  {
    $project: {
      _id: "$_newsId",
      dgubun: "$DGUBUN",
      title: "$TITLE",
      seqno: "$SEQNO",
      newscode_ts: { $toLong: "$_date" },
      kind: ["$KIND", "$KIND2"],
      shcodeTop: "$SHCODE",
    },
  },
]
```

### 변경 후

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

### 변경 이유

`news_cont_*` lookup에서 `YMD`, `NEWSCODE`, `SEQNO`가 필요하므로 `NEWS_MAST`에서 읽은 값을 임시 문서에 보존한다.

추가된 필드:

```js
ymd: "$YMD"
newscode: "$NEWSCODE"
```

## 변경 2. newsid2contid에 ymd/newscode 전달

### 기존

```js
{
  _id: 0,
  seqno: 1,
  parent: "$_id",
  oidrand: { ... }
}
```

### 변경 후

```js
{
  _id: 0,
  ymd: 1,
  seqno: 1,
  newscode: 1,
  parent: "$_id",
  oidrand: { ... }
}
```

### 변경 이유

`migrate_cont` 단계에서 content lookup을 수행하기 전까지 `ymd`, `seqno`, `newscode`를 유지해야 한다.

## 변경 3. migrate_cont lookup 조건 변경

### 기존 조건

기존에는 `SEQNO` 하나만으로 본문을 찾았다.

```js
$eq: ["$SEQNO", "$$seq"]
```

즉 기존 join 기준은 다음이었다.

```text
NEWS_MAST.SEQNO = NEWS_CONT_*.SEQNO
```

### 변경 후 조건

변경 후에는 `YMD`는 반드시 같아야 하고, `NEWSCODE` 또는 `SEQNO`가 매칭되어야 한다.

```text
NEWS_MAST.YMD = NEWS_CONT_*.YMD
AND
(
  NEWS_MAST.NEWSCODE = NEWS_CONT_*.NEWSCODE
  OR
  NEWS_MAST.SEQNO = NEWS_CONT_*.SEQNO
)
```

코드:

```js
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
```

`YMD`, `SEQNO`, `NEWSCODE`는 모두 문자열로 들어오는 것이 확인되어 `$toString` 변환은 사용하지 않는다.

## 변경 4. match priority 적용

`YMD + NEWSCODE`를 1순위로, `YMD + SEQNO`를 2순위로 선택하기 위해 `_matchPriority`를 추가했다.

```js
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
```

의미:

| `_matchPriority` | 의미 |
|---:|---|
| 1 | `YMD + NEWSCODE` 매칭 |
| 2 | `YMD + SEQNO` fallback 매칭 |

## 변경 5. priority와 LINENO 기준 정렬

```js
$sort: {
  _matchPriority: 1,
  LINENO: 1
}
```

정렬 의미:

```text
1. NEWSCODE 매칭 결과를 먼저 둔다.
2. 같은 priority 안에서는 LINENO 순서로 CONTENT를 배열화한다.
```

## 변경 6. priority별 group 후 1순위만 선택

```js
$group: {
  _id: "$_matchPriority",
  contents: {
    $push: "$CONTENT"
  }
}
```

그 다음 priority가 가장 높은 그룹만 선택한다.

```js
{ $sort: { _id: 1 } },
{ $limit: 1 }
```

이렇게 하면 `YMD + NEWSCODE` 결과가 있으면 그 결과만 사용하고, 없을 때만 `YMD + SEQNO` 결과를 사용한다.

## 변경 7. SEQNO 비교 단순화

고객 데이터에서 `YMD`, `SEQNO`, `NEWSCODE`가 모두 문자열로 들어오는 것이 확인되었다.

따라서 `SEQNO` 비교는 padding이나 `$toString` 변환 없이 직접 비교한다.

```js
{ $eq: ["$SEQNO", "$$seq"] }
```

전제:

```text
NEWS_MAST.SEQNO와 NEWS_CONT_*.SEQNO 모두 문자열
앞자리 0도 문자열 값으로 보존됨
```

## 최종 동작 요약

최종 content lookup 흐름은 다음과 같다.

```text
1. NEWS_MAST에서 YMD, SEQNO, NEWSCODE를 유지한다.
2. NEWS_CONT_*에서 같은 YMD를 찾는다.
3. 같은 YMD 안에서 NEWSCODE가 같으면 1순위로 선택한다.
4. NEWSCODE 매칭이 없으면 SEQNO가 같은 항목을 2순위로 선택한다.
5. 선택된 결과를 LINENO 오름차순으로 정렬한다.
6. CONTENT를 배열로 만든다.
7. 최종 target collection에 merge한다.
```

## 권장 인덱스

성능을 위해 `news_cont_*` 컬렉션마다 아래 인덱스를 권장한다.

```js
db.news_cont_p.createIndex({ YMD: 1, NEWSCODE: 1, LINENO: 1 })
db.news_cont_p.createIndex({ YMD: 1, SEQNO: 1, LINENO: 1 })
```

`CO_CONT_LIST`에 여러 collection이 있으면 각각 생성한다.

```js
db.news_cont_i.createIndex({ YMD: 1, NEWSCODE: 1, LINENO: 1 })
db.news_cont_i.createIndex({ YMD: 1, SEQNO: 1, LINENO: 1 })
```

## 검증 쿼리

### YMD + NEWSCODE 매칭 확인

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

### YMD + SEQNO 매칭 확인

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

## 수정 확인

`pipeline.js` 구문 확인을 완료했다.

```sh
node --check pipeline.js
```

결과:

```text
no output, syntax OK
```
