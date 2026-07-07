# KB POC Migration

MongoDB `news_mast`, `news_jmcode`, `news_cont_*` 컬렉션을 변환해 `news_mig` 컬렉션으로 이관하는 Node.js 기반 마이그레이션 프로젝트입니다.

이 프로젝트는 ESM 방식으로 작성되어 있으며, 마이그레이션 실행 파일과 재사용 가능한 함수 모듈을 함께 제공합니다.

## Requirements

- Node.js 20 이상
- npm
- MongoDB 접속 URI
- 대상 MongoDB 컬렉션의 권한: read, write, createCollection, update

## Files

- `migrate.js`: 마이그레이션 실행 진입점
- `mast_jmcode.js`: `news_mast`와 `news_jmcode` 변환 및 병합 로직
- `cont.js`: 본문 컬렉션(`news_cont_*`) 이관 로직
- `pipeline.js`: MongoDB aggregation pipeline 정의
- `.env.example`: 실행 환경변수 예시

## Setup

```sh
npm install
cp .env.example .env
```

`.env` 파일을 열어 MongoDB 접속 정보와 컬렉션 이름을 환경에 맞게 수정합니다.

```env
MONGODB_URI=mongodb+srv://<user>:<password>@<cluster-host>/

nWORKERS=8 # no of parallel workers
BATCH_SIZE=50 # no of docs to process per batch

NEWSDB=newsdb

CO_MAST=news_mast # news title collection
CO_JMCODE=news_jmcode # news title:jmcode pivot table (1:N)
CO_CONT_LIST=news_cont_p #,news_cont_q - comma-separated news content collections
CO_TO=news_mig # the final migration target collection

CO_CHECKPOINT=checkpoint # to pick up where the migration left off
```

## Run Migration

```sh
node migrate.js
```

실행하면 다음 작업을 수행합니다.

1. `MONGODB_URI`로 MongoDB에 접속합니다.
2. `CO_TO` 컬렉션이 없으면 clustered index 기반으로 생성합니다.
3. `news_mast` 문서를 `nWORKERS` 개의 범위로 나누고 checkpoint를 생성합니다.
4. 각 worker가 담당 범위의 문서를 batch 단위로 변환합니다.
5. `news_jmcode`와 본문 컬렉션을 조인해 `news_mig`에 병합합니다.
6. 진행 상태를 checkpoint 컬렉션에 저장합니다.

중간에 `Ctrl+C`를 누르면 진행 중인 작업을 정리하고 종료합니다. 다시 실행하면 checkpoint 기준으로 이어서 처리합니다(idempotent operation).

## Exported Functions

ESM import 방식으로 마이그레이션 함수를 외부 모듈에서 사용할 수 있습니다.

```js
import {
  migrate_news,
  createProgressBar,
  abortMigration,
} from "./mast_jmcode.js";
```

주요 export는 다음과 같습니다.

- `migrate_news(db, cp, pbar)`: checkpoint 하나에 대한 뉴스 마이그레이션 수행
- `createProgressBar(cp, cursor_y, startTime)`: worker별 진행률 출력 함수 생성
- `abortMigration()`: 진행 중인 마이그레이션 중단 플래그 설정

본문 컬렉션 이관 함수도 별도로 import할 수 있습니다.

```js
import { migrate_conts } from "./cont.js";
```

## Checkpoint

checkpoint 컬렉션에는 `_id`가 `migrator_1`, `migrator_2` 형식인 문서가 저장됩니다.

worker 수(`nWORKERS`)와 checkpoint 문서 수가 다르면 기존 `migrator_*` checkpoint를 삭제하고 새로 생성합니다.

checkpoint를 완전히 초기화하려면 MongoDB에서 다음 문서를 삭제한 뒤 다시 실행합니다.

```js
db.checkpoint.deleteMany({ _id: /^migrator_/ });
```

## Index Notes

성능을 위해 다음 인덱스를 준비하는 것이 좋습니다.

```js
db.news_jmcode.createIndex({ SEQNO: 1 });
db.news_cont_p.createIndex({ SEQNO: 1, LINENO: 1 });
```

`CO_CONT_LIST`에 여러 본문 컬렉션을 지정하는 경우 각 컬렉션에 `(SEQNO, LINENO)` 복합 인덱스를 생성합니다.

## Troubleshooting

- `MONGODB_URI` 오류: `.env` 파일의 URI, 계정, IP allowlist를 확인합니다.
- checkpoint 개수가 worker 수와 다름: 프로그램이 `migrator_*` checkpoint를 재생성합니다.
- 진행률 표시가 깨짐: 터미널 높이가 `nWORKERS + 2` 줄 이상인지 확인합니다.
- 조인 성능 저하: `news_jmcode.SEQNO`, 본문 컬렉션의 `(SEQNO, LINENO)` 인덱스를 확인합니다.

## 수정사항 by SM
1. newscode_ts 정확한 로직 확인
즉 pipeline.js의 이 부분:
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
수정 후:
transform_tmp: [
  {
    $project: {
      _id: "$_newsId",
      dgubun: "$DGUBUN",
      title: "$TITLE",
      seqno: "$SEQNO",
      newscode_ts: "$_date",
      kind: ["$KIND", "$KIND2"],
      shcodeTop: "$SHCODE",
    },
  },
]
정리하면:
Date 변환 로직은 있다.
하지만 최종 저장 직전에 $toLong으로 숫자로 바꾸고 있다.

2. shcode 가 object 배열로 추가되는 부분 
   shcodeTop: "$SHCODE"
   
<img width="439" height="265" alt="image" src="https://github.com/user-attachments/assets/adb63c18-6a33-43f9-bdfa-fed510a09e23" />

3. 검색이 안되는 시나리오 생김
   원인은 인덱스가 아니라 news_mig_500의 문서 구조 때문입니다.
이미지 기준으로 news_mig_500은 뉴스 1건이 2개 문서로 나뉘어 있습니다.
문서 1: title, dgubun, shcode 있음
문서 2: parent, contents 있음
예:
{
  _id: ObjectId("69553a705683d88cc08007b3"),
  dgubun: "4",
  title: "삼성전자, 반도체 업황 회복 기대에 강세",
  shcode: [
    { shcode: "005930", expcode: "A005930" }
  ]
}
그리고 contents는 별도 문서입니다.
{
  _id: ObjectId("69553a705683d88cc18007b3"),
  parent: ObjectId("69553a705683d88cc08007b3"),
  contents: [
    "...삼성전자...",
    "...실적..."
  ]
}
그래서 이 조건은 한 문서 안에서 동시에 만족되지 않습니다.
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
실제로 확인하면:
"삼성전자" + shcode.shcode=005930 -> 결과 있음
"실적" + shcode.shcode=005930 -> 결과 있음
"삼성전자 실적" + shcode.shcode=005930 + matchCriteria all -> 결과 없음
"삼성전자 실적" 필터 없음 -> contents 문서에서 결과 있음
즉 contents 문서에는 "삼성전자 실적"이 있지만 shcode가 없고, shcode 문서에는 contents가 없습니다.
해결 방법은 3가지입니다.
1. 현재 news_mig_500 구조를 유지하고 검색어를 단순화
query: "삼성전자"
또는:
query: "실적"
2. matchCriteria: "all" 제거
이러면 "삼성전자 실적" 중 일부 토큰만 맞아도 결과가 나올 수 있습니다.
text: {
  query: "삼성전자 실적",
  path: ["title", "contents"]
}
다만 정확도는 낮아집니다.
3. 권장: unified migration 결과 컬렉션 사용
title, shcode, contents가 한 document에 모두 들어가는 구조가 필요합니다.
{
  title: "...",
  shcode: [{ shcode: "005930" }],
  contents: ["...", "..."]
}
이 구조여야 아래 쿼리가 의도대로 동작합니다.
query: "삼성전자 실적"
path: ["title", "contents"]
filter: shcode.shcode = "005930"
결론:
news5_search_index는 READY이고 shcode.shcode path도 맞습니다.
결과가 안 나오는 이유는 title/shcode와 contents가 서로 다른 document에 분리되어 있기 때문입니다.
삼성전자 실적 + 005930 조건을 제대로 검증하려면 news_mig_500_unified 같은 통합 document 컬렉션을 만들어서 그 컬렉션에 Search Index를 생성해야 합니다.
