# Oracle JSON_OBJECT Export 후처리 스크립트

Oracle 12c R2에서 `JSON_OBJECT()`로 export한 결과 중 문자열 값에 큰따옴표가 빠진 데이터를 MongoDB import 가능한 JSON Lines로 복구하는 스크립트다.

## 생성 파일

```text
repair_json_common.py
repair_news_mast_json.py
repair_news_jmcode_json.py
repair_news_cont_p_json.py
JSON_REPAIR_README.md
```

## 기준 DDL

`char` 디렉토리의 DDL을 기준으로 컬럼 타입을 고정했다.

```text
create_news_mast.txt
create_news_jmcode.txt
create_news_cont_p.txt
```

## 컬럼 처리 기준

### NEWS_MAST

모든 컬럼을 문자열 또는 null로 처리한다.

```text
DGUBUN, YMD, SEQNO, NEWSCODE, KIND, KIND2, TITLE, SHCODE
```

### NEWS_JMCODE

모든 컬럼을 문자열 또는 null로 처리한다.

```text
DGUBUN, YMD, SEQNO, SHCODE, EXPCODE, NEWSCODE, KIND
```

### NEWS_CONT_P

`LINENO`만 숫자로 처리하고 나머지는 문자열 또는 null로 처리한다.

```text
YMD, SEQNO, NEWSCODE, LINENO, CONTENT
```

## CONTENT/TITLE 내부 큰따옴표 처리

`TITLE`, `CONTENT` 값 안에 큰따옴표가 포함되어 있으면 JSON에서는 `\"`로 escape되어야 한다.

예:

```text
원본: "CONTENT":"트럼프 "관세" 발언"
정상: "CONTENT":"트럼프 \"관세\" 발언"
```

이 스크립트는 값을 Python 문자열로 복구한 뒤 최종 출력 시 `json.dumps()`를 사용한다.

따라서 문자열 내부의 큰따옴표, 역슬래시, 줄바꿈, 탭 등은 JSON 형식에 맞게 자동 escape된다.

## 사용법

`char` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc/char
```

### NEWS_MAST 변환

```sh
python repair_news_mast_json.py \
  --input raw/news_mast_bad.json \
  --output fixed/news_mast_fixed.jsonl
```

### NEWS_JMCODE 변환

```sh
python repair_news_jmcode_json.py \
  --input raw/news_jmcode_bad.json \
  --output fixed/news_jmcode_fixed.jsonl
```

### NEWS_CONT_P 변환

```sh
python repair_news_cont_p_json.py \
  --input raw/news_cont_p_bad.json \
  --output fixed/news_cont_p_fixed.jsonl
```

## 테스트 실행

처음에는 일부 라인만 테스트하는 것을 권장한다.

```sh
python repair_news_mast_json.py \
  --input raw/news_mast_bad.json \
  --output fixed/news_mast_sample.jsonl \
  --limit 100
```

## Bad row 파일

변환하지 못한 라인은 별도 bad row 파일에 저장된다.

기본 파일명:

```text
<output>.bad.jsonl
```

예:

```text
fixed/news_mast_fixed.jsonl.bad.jsonl
```

bad row에는 원본 라인과 오류 메시지가 저장된다.

```json
{"line_no":123,"error":"missing key: SHCODE","raw":"..."}
```

## 변환 결과 검증

JSON Lines 파일이 정상 JSON인지 확인한다.

```sh
python - <<'PY'
import json
from pathlib import Path

for path in [
    "fixed/news_mast_fixed.jsonl",
    "fixed/news_jmcode_fixed.jsonl",
    "fixed/news_cont_p_fixed.jsonl",
]:
    count = 0
    with Path(path).open(encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            json.loads(line)
            count += 1
    print(path, count)
PY
```

## MongoDB import 예시

```sh
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_mast_fixed --drop --file fixed/news_mast_fixed.jsonl
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_jmcode_fixed --drop --file fixed/news_jmcode_fixed.jsonl
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_cont_p_fixed --drop --file fixed/news_cont_p_fixed.jsonl
```

## 주의사항

이 스크립트는 컬럼 순서가 DDL과 동일하다는 전제를 사용한다.

```text
NEWS_MAST   : DGUBUN, YMD, SEQNO, NEWSCODE, KIND, KIND2, TITLE, SHCODE
NEWS_JMCODE : DGUBUN, YMD, SEQNO, SHCODE, EXPCODE, NEWSCODE, KIND
NEWS_CONT_P : YMD, SEQNO, NEWSCODE, LINENO, CONTENT
```

컬럼 순서가 다르면 스크립트의 `COLUMNS` 값을 수정해야 한다.

`CONTENT`는 마지막 컬럼이라 내부 쉼표나 큰따옴표가 있어도 비교적 안전하게 복구된다.

`TITLE`은 중간 컬럼이므로 값 안에 다음 key delimiter가 그대로 들어가면 bad row로 분리될 수 있다.

```text
,"SHCODE":
```

이런 bad row는 수동 확인이 필요하다.
