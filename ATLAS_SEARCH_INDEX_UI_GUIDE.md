 # Atlas UI Search Index 생성 가이드

이 문서는 MongoDB Atlas UI에서 `news_array` 컬렉션의 Search Index를 생성하는 절차를 정리한다.

## 대상

```text
Database: newsdb
Collection: news_array
Search Index Name: news_search_index
```

현재 테스트 데이터의 주요 필드:

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

## 생성 절차

1. MongoDB Atlas에 접속한다.

```text
https://cloud.mongodb.com
```

2. 테스트 중인 Cluster를 선택한다.
<img width="1300" height="563" alt="image" src="https://github.com/user-attachments/assets/b20e3cb4-7c67-43e0-979f-e14bbce941ea" />

<img width="1263" height="465" alt="image" src="https://github.com/user-attachments/assets/6bf930ee-60c9-4def-bd5a-f2669d0b01e4" />

3. Index 명을 입력
<img width="1269" height="729" alt="image" src="https://github.com/user-attachments/assets/99976106-8c5f-4e2a-a63f-69b8dbca77a4" />

```text
Database > Browse Collections
```

4. Search 대상 컬렉션을 선택

```text
newsdb > news_array
```
<img width="1246" height="754" alt="image" src="https://github.com/user-attachments/assets/a98d415d-d761-401f-bc7b-289b797251ce" />


7. 생성 방식으로 `JSON Editor`를 선택한다. UI가 편할 경우 Visual Editor 선택


9. JSON Editor에 아래 인덱스 정의를 입력한다.

```json
{
  "mappings": {
    "dynamic": false,
    "fields": {
      "title": {
        "type": "string",
        "analyzer": "lucene.nori",
        "searchAnalyzer": "lucene.nori"
      },
      "contents": {
        "type": "string",
        "analyzer": "lucene.nori",
        "searchAnalyzer": "lucene.nori"
      },
      "shcode": {
        "type": "token"
      },
      "dgubun": {
        "type": "token"
      },
      "kind": {
        "type": "token"
      },
      "newscode_ts": {
        "type": "date"
      }
    }
  }
}
```

10. `Create Search Index`를 클릭한다.
<img width="878" height="486" alt="image" src="https://github.com/user-attachments/assets/9faafdfa-76f6-4a50-b661-63e766bbd1d3" />

11. Search Index 상태가 `READY`가 될 때까지 기다린다.



1GB 수준의 데이터이므로 인덱스 생성에 시간이 걸릴 수 있다.

## 필드 매핑 설명

| 필드 | 타입 | 설명 |
|---|---|---|
| `title` | `string` | 뉴스 제목 한국어 검색 |
| `contents` | `string` | 뉴스 본문 한국어 검색. 배열 필드도 인덱싱 가능 |
| `shcode` | `token` | 종목코드 exact filter 검색 |
| `dgubun` | `token` | 뉴스구분 exact filter 검색 |
| `kind` | `token` | kind exact filter 검색 |
| `newscode_ts` | `date` | 최신순 정렬 및 날짜 조건 |

## 주의 사항

컬렉션명은 `news_array`이다.

본문 필드명은 `contents`이다. `content`가 아니다.

`kind`는 소문자이다. `Kind`가 아니다.

`contents`, `shcode`, `kind`는 배열 필드지만 위 매핑으로 Atlas Search 인덱싱이 가능하다.

`READY` 상태가 되기 전에는 `$search` 쿼리가 실패하거나 결과가 정상적으로 나오지 않을 수 있다.

## 생성 확인 쿼리

`mongosh`에서 Search Index 상태를 확인할 수 있다.

```js
use newsdb

db.news_array.aggregate([
  { $listSearchIndexes: { name: "news_search_index" } }
])
```

## 테스트 쿼리

인덱스가 `READY`가 되면 아래 쿼리로 검색을 테스트한다.

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

검색어 없이 Search를 사용하는 전체 조회 테스트는 아래처럼 `exists` filter를 사용한다.

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
