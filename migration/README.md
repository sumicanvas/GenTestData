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
