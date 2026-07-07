# 500MB Small JSON_OBJECT 데이터 MongoDB Atlas 로딩 가이드

`generated_sjson_500mb` 폴더에 생성한 Oracle `JSON_OBJECT()` 형태의 500MB 테스트 데이터를 MongoDB Atlas에 로딩하는 방법을 정리한다.

## 입력 파일

입력 폴더:

```text
kbtestdata/generated_sjson_500mb/
```

입력 파일:

| 파일 | 설명 | 건수 | 크기 |
|---|---|---:|---:|
| `news_sjson_mast.json` | 뉴스 마스터 | 381,794 | 76,304,715 bytes |
| `news_sjson_jmcode.json` | 뉴스-종목 매핑 | 763,587 | 100,029,897 bytes |
| `news_sjson_cont_p.json` | 뉴스 본문 라인 | 1,527,175 | 323,665,638 bytes |

합계 크기:

```text
500,000,250 bytes
```

## 로딩 컬렉션명

요청 기준에 따라 500MB 테스트 데이터는 collection 이름 뒤에 `_500` suffix를 붙인다.

| JSON 파일 | MongoDB 컬렉션 |
|---|---|
| `news_sjson_mast.json` | `news_mast_500` |
| `news_sjson_jmcode.json` | `news_jmcode_500` |
| `news_sjson_cont_p.json` | `news_cont_p_500` |

## 로딩 명령

아래 명령은 `kbtestdata` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbtestdata
```

### NEWS_MAST

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --db newsdb \
  --collection news_mast_500 \
  --drop \
  --file generated_sjson_500mb/news_sjson_mast.json
```

### NEWS_JMCODE

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --db newsdb \
  --collection news_jmcode_500 \
  --drop \
  --file generated_sjson_500mb/news_sjson_jmcode.json
```

### NEWS_CONT_P

```sh
mongoimport \
  --uri "$MONGODB_URI" \
  --db newsdb \
  --collection news_cont_p_500 \
  --drop \
  --file generated_sjson_500mb/news_sjson_cont_p.json
```

## 한 번에 실행

```sh
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_mast_500 --drop --file generated_sjson_500mb/news_sjson_mast.json
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_jmcode_500 --drop --file generated_sjson_500mb/news_sjson_jmcode.json
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_cont_p_500 --drop --file generated_sjson_500mb/news_sjson_cont_p.json
```

## 로딩 후 검증

`mongosh`로 접속한다.

```sh
mongosh "$MONGODB_URI"
```

건수를 확인한다.

```js
db.news_mast_500.countDocuments()
db.news_jmcode_500.countDocuments()
db.news_cont_p_500.countDocuments()
```

예상 건수:

```text
news_mast_500   : 381794
news_jmcode_500 : 763587
news_cont_p_500 : 1527175
```

샘플 문서를 확인한다.

```js
db.news_mast_500.findOne({}, { _id: 0 })
db.news_jmcode_500.findOne({}, { _id: 0 })
db.news_cont_p_500.findOne({}, { _id: 0 })
```

공통 key가 유지되는지 확인한다.

```js
db.news_mast_500.findOne(
  { DGUBUN: "4", YMD: "20260101", SEQNO: "00000000" },
  { _id: 0 }
)

db.news_jmcode_500.find(
  { DGUBUN: "4", YMD: "20260101", SEQNO: "00000000" },
  { _id: 0 }
)

db.news_cont_p_500.find(
  { DGUBUN: "4", YMD: "20260101", SEQNO: "00000000" },
  { _id: 0 }
).sort({ LINENO: 1 })
```

## Migration .env 예시

500MB 데이터를 migration source로 사용할 때는 `.env`를 아래처럼 설정한다.

```env
CO_MAST=news_mast_500
CO_JMCODE=news_jmcode_500
CO_CONT_LIST=news_cont_p_500
CO_TO=news_mig_500
CO_CHECKPOINT=checkpoint_500
```

통합 document 버전 migration을 사용할 경우 target 이름을 분리하는 것을 권장한다.

```env
CO_TO=news_mig_500_unified
CO_CHECKPOINT=checkpoint_500_unified
```

## 주의사항

`--drop` 옵션은 동일 이름의 기존 collection을 삭제한 뒤 다시 로딩한다.

기존 데이터를 보존해야 하면 `--drop`을 제거하거나 다른 collection 이름을 사용한다.
