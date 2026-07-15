# news_mig contents 필드 상태 확인 MQL

`news_mig` 컬렉션에서 `contents` 필드가 없거나 비어 있는 문서 수를 확인하는 MQL이다.

## 대상

```text
Database: newsdb
Collection: news_mig
```

## contents 필드가 없는 문서 수

```js
db.news_mig.countDocuments({
  contents: { $exists: false }
});
```

## contents 필드는 있지만 null인 문서 수

```js
db.news_mig.countDocuments({
  contents: null
});
```

주의: MongoDB에서 `{ contents: null }`은 `contents`가 `null`인 문서와 `contents` 필드가 없는 문서를 모두 매칭할 수 있다.

`null`만 정확히 보려면 아래처럼 확인한다.

```js
db.news_mig.countDocuments({
  contents: { $type: "null" }
});
```

## contents가 빈 배열인 문서 수

```js
db.news_mig.countDocuments({
  contents: { $type: "array", $size: 0 }
});
```

## contents가 없거나 null이거나 빈 배열인 문서 수

```js
db.news_mig.countDocuments({
  $or: [
    { contents: { $exists: false } },
    { contents: { $type: "null" } },
    { contents: { $type: "array", $size: 0 } }
  ]
});
```

## 상태별 집계

```js
db.news_mig.aggregate([
  {
    $facet: {
      missing_contents: [
        { $match: { contents: { $exists: false } } },
        { $count: "count" }
      ],
      null_contents: [
        { $match: { contents: { $type: "null" } } },
        { $count: "count" }
      ],
      empty_array_contents: [
        { $match: { contents: { $type: "array", $size: 0 } } },
        { $count: "count" }
      ],
      non_empty_array_contents: [
        {
          $match: {
            contents: { $type: "array" },
            $expr: { $gt: [{ $size: "$contents" }, 0] }
          }
        },
        { $count: "count" }
      ]
    }
  }
]);
```

## title 문서와 contents 문서 구분해서 확인

`news_mig`가 split document 구조라면 보통 다음과 같은 형태일 수 있다.

```text
title/shcode 문서: title 있음, contents 없음
contents 문서: parent 있음, contents 있음
```

title 문서 중 contents가 없는 문서 수:

```js
db.news_mig.countDocuments({
  title: { $exists: true },
  contents: { $exists: false }
});
```

contents 문서 수:

```js
db.news_mig.countDocuments({
  parent: { $exists: true },
  contents: { $exists: true }
});
```

title과 contents가 둘 다 있는 문서 수:

```js
db.news_mig.countDocuments({
  title: { $exists: true },
  contents: { $exists: true }
});
```

## 샘플 문서 확인

`contents`가 없거나 비어 있는 문서 샘플:

```js
db.news_mig.find(
  {
    $or: [
      { contents: { $exists: false } },
      { contents: { $type: "null" } },
      { contents: { $type: "array", $size: 0 } }
    ]
  },
  {
    _id: 1,
    title: 1,
    parent: 1,
    contents: 1,
    dgubun: 1,
    shcode: 1
  }
).limit(10);
```

`contents`가 있는 문서 샘플:

```js
db.news_mig.find(
  {
    contents: { $exists: true, $type: "array" },
    $expr: { $gt: [{ $size: "$contents" }, 0] }
  },
  {
    _id: 1,
    parent: 1,
    contents: 1
  }
).limit(10);
```

## 참고

`contents` 필드가 없다고 해서 반드시 오류는 아니다.

현재 `news_mig`가 split document 구조라면 title 문서에는 `contents`가 없고, 별도의 child 문서에 `contents`가 들어갈 수 있다.

따라서 단순히 `contents` missing count만 보지 말고 `title`, `parent` 필드와 함께 구조를 확인해야 한다.
