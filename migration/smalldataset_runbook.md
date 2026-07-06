# Small JSON 테스트 데이터 마이그레이션 실행 정리

`news_sjson_*` 컬렉션 3개를 source로 사용해 `node migrate.js`를 실행하고, 하나의 target 컬렉션으로 이관한 과정을 정리한다.

이 문서는 작은 테스트 데이터 1000건 기준의 실행 기록과 재실행 방법을 설명한다.

## 목적

Oracle 원천 구조는 3개 테이블로 구성되어 있다.

```text
NEWS_MAST    : 뉴스 제목/마스터
NEWS_JMCODE  : 뉴스-종목 매핑
NEWS_CONT_P  : 뉴스 본문 라인
```

MongoDB에는 Oracle `JSON_OBJECT()` export와 유사한 JSON Lines 파일을 로딩해 아래 3개 collection으로 준비했다.

```text
news_sjson_mast
news_sjson_jmcode
news_sjson_cont_p
```

`kbpoc/migration/node migrate.js`는 이 3개 collection을 읽어 target collection으로 이관한다.

현재 target collection은 다음이다.

```text
news_sjson_mig
```

## 실행 위치

마이그레이션 코드는 아래 폴더에 있다.

```text
/Users/sumi.ryu/Documents/opencode/kbpoc/migration
```

주요 파일:

| 파일 | 역할 |
|---|---|
| `migrate.js` | 마이그레이션 실행 진입점 |
| `mast_jmcode.js` | `NEWS_MAST` 변환, `NEWS_JMCODE` lookup, checkpoint 업데이트 |
| `cont.js` | 본문 collection lookup 실행 |
| `pipeline.js` | aggregation pipeline 정의 |
| `.env` | 실행 환경변수 |

## 현재 .env 설정

작은 테스트 데이터 기준 `.env`는 아래 source/target을 사용한다.

```env
NEWSDB=newsdb

CO_MAST=news_sjson_mast
CO_JMCODE=news_sjson_jmcode
CO_CONT_LIST=news_sjson_cont_p
CO_TO=news_sjson_mig
CO_CHECKPOINT=checkpoint_sjson
```

작은 테스트 데이터와 대용량 테스트 데이터를 섞지 않기 위해 `CO_TO`, `CO_CHECKPOINT`도 별도 이름을 사용한다.

| 목적 | 작은 테스트용 이름 |
|---|---|
| 마스터 source | `news_sjson_mast` |
| 종목 매핑 source | `news_sjson_jmcode` |
| 본문 source | `news_sjson_cont_p` |
| 마이그레이션 target | `news_sjson_mig` |
| checkpoint | `checkpoint_sjson` |

## Source 데이터

작은 테스트 데이터는 `kbtestdata/generated_sjson_1000/` 아래 JSON Lines 파일로 생성했다.

Atlas에는 다음 collection으로 로딩되어 있다.

| collection | 건수 | 설명 |
|---|---:|---|
| `news_sjson_mast` | 1,000 | 뉴스 마스터 |
| `news_sjson_jmcode` | 1,999 | 뉴스별 종목 매핑 |
| `news_sjson_cont_p` | 3,999 | 뉴스 본문 라인 |

각 collection에는 공통 업무 key가 들어 있다.

```text
DGUBUN
YMD
SEQNO
```

현재 migration 코드는 기존 설계대로 `SEQNO`만 사용해 lookup한다.

## 실행 전 인덱스

조인 성능을 위해 실행 전에 아래 인덱스를 생성했다.

```js
db.news_sjson_jmcode.createIndex({ SEQNO: 1 })
db.news_sjson_cont_p.createIndex({ SEQNO: 1, LINENO: 1 })
```

Node.js에서 실행한 명령은 다음이다.

```sh
node --input-type=module -e 'import "dotenv/config"; import { MongoClient } from "mongodb"; const client = new MongoClient(process.env.MONGODB_URI); await client.connect(); const db = client.db(process.env.NEWSDB); console.log(await db.collection(process.env.CO_JMCODE).createIndex({ SEQNO: 1 })); for (const name of (process.env.CO_CONT_LIST || "").split(",").map(s => s.trim()).filter(Boolean)) { console.log(await db.collection(name).createIndex({ SEQNO: 1, LINENO: 1 })); } await client.close();'
```

## 실행 명령

마이그레이션 폴더로 이동한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc/migration
```

마이그레이션을 실행한다.

```sh
node migrate.js
```

## 실행 로그 요약

실행 시 target collection이 없으면 새로 생성한다.

```text
Creating migration target collection: news_sjson_mig
```

checkpoint가 없으면 worker 수만큼 checkpoint를 생성한다.

```text
Checkpoint count (0) does not match number of workers (8). Resetting checkpoints...
Dividing 1000 documents into 8 buckets...
```

8개 worker 기준으로 source `news_sjson_mast` 1000건을 분할 처리한다.

```text
Starting migration with 8 workers...
migrator_1 start (...) nDocs=125
migrator_2 start (...) nDocs=125
...
migrator_8 start (...) nDocs=125
```

완료 로그는 다음과 같은 형태다.

```text
migrator_4: Migration Completed: 125
migrator_2: Migration Completed: 125
migrator_1: Migration Completed: 126
...
```

## 실행 결과

실행 후 검증 결과는 다음과 같다.

| 항목 | 결과 |
|---|---:|
| `news_sjson_mast` | 1,000 |
| `news_sjson_jmcode` | 1,999 |
| `news_sjson_cont_p` | 3,999 |
| `news_sjson_mig` 전체 문서 | 2,000 |
| `title` 포함 문서 | 1,000 |
| `contents` 포함 문서 | 1,000 |
| `title`과 `contents`를 모두 포함한 문서 | 0 |
| checkpoint processed | 1,000 / 1,000 |

검증 쿼리는 다음과 같다.

```js
db.news_sjson_mast.countDocuments()
db.news_sjson_jmcode.countDocuments()
db.news_sjson_cont_p.countDocuments()
db.news_sjson_mig.countDocuments()
db.news_sjson_mig.countDocuments({ title: { $exists: true } })
db.news_sjson_mig.countDocuments({ contents: { $exists: true } })
db.news_sjson_mig.countDocuments({ title: { $exists: true }, contents: { $exists: true } })
```

checkpoint 검증:

```js
db.checkpoint_sjson.aggregate([
  { $match: { _id: /^migrator_/ } },
  {
    $group: {
      _id: null,
      processed: { $sum: "$nDocsProcessed" },
      expected: { $sum: "$nDocs2Process" }
    }
  }
])
```

예상 결과:

```js
[{ _id: null, processed: 1000, expected: 1000 }]
```

## Target 구조 주의사항

현재 migration 코드는 `NEWS_MAST + NEWS_JMCODE` 결과와 `NEWS_CONT_P` 결과를 같은 target collection에 넣지만, 하나의 document로 합치지는 않는다.

즉 뉴스 1건마다 target에 2개 document가 생긴다.

```text
1. master/jmcode document
2. contents document
```

따라서 source `NEWS_MAST` 1000건 기준 target은 총 2000건이 된다.

```text
1000 master/jmcode documents + 1000 contents documents = 2000 documents
```

master/jmcode document 예시는 다음과 같다.

```js
{
  _id: ObjectId("..."),
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

contents document 예시는 다음과 같다.

```js
{
  _id: ObjectId("..."),
  contents: [
    "<div class=\"news\"><p><strong>삼성전자</strong>...",
    "증권가는 외국인 수급과 분기 실적 전망을..."
  ]
}
```

현재 구조에서는 아래 조건의 문서 수가 0이다.

```js
db.news_sjson_mig.countDocuments({
  title: { $exists: true },
  contents: { $exists: true }
})
```

## 현재 코드 흐름

### 1. migrate.js

`migrate.js`는 `.env`를 읽고 MongoDB에 접속한다.

주요 작업:

1. `CO_TO` collection 생성
2. `CO_CHECKPOINT`에서 checkpoint 조회
3. checkpoint가 worker 수와 다르면 checkpoint 재생성
4. source `CO_MAST`를 `_id` 기준으로 bucket 분할
5. worker별로 `migrate_news()` 실행

### 2. mast_jmcode.js

`migrate_news()`는 checkpoint 범위 안에서 batch 단위로 `CO_MAST`를 읽는다.

주요 작업:

1. batch 조회
2. `NEWSCODE`를 날짜 값으로 변환
3. `ObjectId` 생성
4. `CO_JMCODE` lookup
5. target `CO_TO`에 `$merge`
6. contents 이관 호출
7. checkpoint 업데이트

### 3. cont.js

`CO_CONT_LIST`에 지정된 본문 collection 목록을 순회하며 contents 이관을 실행한다.

현재 설정에서는 하나만 사용한다.

```env
CO_CONT_LIST=news_sjson_cont_p
```

### 4. pipeline.js

aggregation pipeline을 정의한다.

중요한 lookup 기준은 현재 `SEQNO`다.

```js
$eq: ["$SEQNO", "$$seq"]
```

`DGUBUN/YMD/SEQNO` 복합키가 source에 존재하지만, 현재 migration 코드에서는 기존 의도대로 `SEQNO`만 사용한다.

## 변경된 코드

이번 실행을 위해 현재 코드에는 아래 변경이 반영되어 있다.

### `.env`

작은 테스트 collection 기준으로 source/target/checkpoint를 설정했다.

```env
CO_MAST=news_sjson_mast
CO_JMCODE=news_sjson_jmcode
CO_CONT_LIST=news_sjson_cont_p
CO_TO=news_sjson_mig
CO_CHECKPOINT=checkpoint_sjson
```

### `migrate.js`

비대화형 실행 환경에서 `process.stdout.moveCursor` 오류가 나지 않도록 TTY 체크가 추가되어 있다.

이 변경은 터미널 progress bar 출력만 안전하게 처리하기 위한 것이며, migration 데이터 변환 로직에는 영향을 주지 않는다.

### `mast_jmcode.js`

TTY가 아닌 환경에서는 progress bar cursor 이동을 하지 않도록 처리되어 있다.

이 변경도 화면 출력 안정화를 위한 것이다.

### `pipeline.js`

본문 lookup 대상 collection이 하드코딩 `news_cont_p`가 아니라 `CO_CONT_LIST` 기반으로 동작하도록 변경되어 있다.

```js
from: process.env.CO_CONT_LIST?.split(",")[0]?.trim() || "news_cont_p"
```

content document용 ObjectId 생성 시 hex 길이가 24자가 안 되는 문제를 막기 위해 padding 처리도 추가되어 있다.

## 재실행 방법

이미 완료된 checkpoint가 있으면 `node migrate.js`는 checkpoint 기준으로 이어서 실행한다.

작은 테스트 migration을 처음부터 다시 하고 싶으면 target과 checkpoint를 삭제한 뒤 재실행한다.

```js
db.news_sjson_mig.drop()
db.checkpoint_sjson.drop()
```

그 다음 다시 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc/migration
node migrate.js
```

## 참고

최종 목표가 뉴스 1건당 하나의 document에 `title`, `shcode`, `contents`를 모두 넣는 구조라면 현재 pipeline은 추가 수정이 필요하다.

현재 결과는 다음 구조다.

```text
뉴스 1건 -> target 2 documents
```

최종 통합 구조를 원하면 다음 구조로 바꾸는 것이 맞다.

```text
뉴스 1건 -> target 1 document
title + shcode + contents 배열 포함
```

이 경우 `mast/jmcode` merge와 `contents` merge를 별도 `_id` 문서로 만들지 않고, 같은 `_id`에 `contents`를 update/merge하도록 pipeline을 변경해야 한다.
