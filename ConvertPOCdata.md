# Oracle JSON_OBJECT Export 후처리 스크립트

Oracle 12c R2에서 `JSON_OBJECT()`로 export한 결과 중 문자열 값에 큰따옴표가 빠진 데이터를 MongoDB import 가능한 JSON Lines로 복구하는 스크립트다.

## 폴더 구조

가독성을 위해 입력과 출력을 아래 폴더로 나눈다.

```text
char/
  input/
    news_mast.json
    news_jmcode.json
    news_cont_p.json
  output/
    news_mast.json
    news_jmcode.json
    news_cont_p.json
    bad/
      news_mast.bad.json
      news_jmcode.bad.json
      news_cont_p.bad.json
```

입력 파일은 `input/` 아래에 둔다.

출력 파일은 기본적으로 `output/` 아래에 입력 파일과 같은 이름의 `.json` 확장자로 저장된다.

예:

```text
input/news_mast.json -> output/news_mast.json
input/news_jmcode.json -> output/news_jmcode.json
input/news_cont_p.json -> output/news_cont_p.json
```

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

### 1. 입력 파일 배치

Oracle에서 받은 파일을 `input/` 폴더에 넣는다.

```text
input/news_mast.json
input/news_jmcode.json
input/news_cont_p.json
```

### 2. NEWS_MAST 변환

```sh
python repair_news_mast_json.py --input input/news_mast.json
```

출력:

```text
output/news_mast.json
output/bad/news_mast.bad.json
```

### 3. NEWS_JMCODE 변환

```sh
python repair_news_jmcode_json.py --input input/news_jmcode.json
```

출력:

```text
output/news_jmcode.json
output/bad/news_jmcode.bad.json
```

### 4. NEWS_CONT_P 변환

```sh
python repair_news_cont_p_json.py --input input/news_cont_p.json
```

출력:

```text
output/news_cont_p.json
output/bad/news_cont_p.bad.json
```

## 출력 파일명 규칙

기본 규칙은 다음과 같다.

```text
input/<원본파일명>.json -> output/<원본파일명>.json
```

예:

```text
input/news_mast.json -> output/news_mast.json
```

입력 파일 확장자가 `.txt`여도 출력은 `.json`으로 저장된다.

```text
input/news_mast.txt -> output/news_mast.json
```

원하는 출력 경로를 직접 지정할 수도 있다.

```sh
python repair_news_mast_json.py \
  --input input/news_mast.json \
  --output output/custom_news_mast.json
```

## 테스트 실행

처음에는 일부 라인만 테스트하는 것을 권장한다.

```sh
python repair_news_mast_json.py \
  --input input/news_mast.json \
  --limit 100
```

## Bad row 파일

변환하지 못한 라인은 별도 bad row 파일에 저장된다.

기본 위치:

```text
output/bad/<원본파일명>.bad.json
```

예:

```text
output/bad/news_mast.bad.json
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
    "output/news_mast.json",
    "output/news_jmcode.json",
    "output/news_cont_p.json",
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

출력 파일 확장자는 `.json`이지만 내용은 JSON Lines 형식이다.

`mongoimport`는 기본적으로 JSON Lines를 처리할 수 있으므로 `--jsonArray`는 사용하지 않는다.

```sh
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_mast_fixed --drop --file output/news_mast.json
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_jmcode_fixed --drop --file output/news_jmcode.json
mongoimport --uri "$MONGODB_URI" --db newsdb --collection news_cont_p_fixed --drop --file output/news_cont_p.json
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

## Troubleshooting

### NEWS_JMCODE가 `missing next key delimiter: KIND2`로 bad 처리되는 경우

`NEWS_JMCODE`에는 `KIND2` 컬럼이 없다.

따라서 아래 오류가 나오면 `NEWS_JMCODE` 파일을 `NEWS_MAST` 스크립트로 처리했거나, 이전 버전 스크립트로 생성된 bad 파일을 보고 있을 가능성이 높다.

```text
missing next key delimiter: KIND2
```

올바른 실행:

```sh
python repair_news_jmcode_json.py --input input/news_jmcode.json
```

### NEWS_CONT_P가 `missing key: DGUBUN`으로 bad 처리되는 경우

`NEWS_CONT_P` DDL에는 `DGUBUN` 컬럼이 없다.

따라서 아래 오류가 나오면 `NEWS_CONT_P` 파일을 `NEWS_MAST` 또는 `NEWS_JMCODE` 스크립트로 처리했거나, 이전 버전 스크립트로 생성된 bad 파일을 보고 있을 가능성이 높다.

```text
missing key: DGUBUN
```

올바른 실행:

```sh
python repair_news_cont_p_json.py --input input/news_cont_p.json
```

### bad 파일이 이전 결과인지 확인

스크립트는 실행할 때마다 output 파일과 bad 파일을 새로 쓴다.

혼동을 피하려면 아래 순서로 다시 실행한다.

```sh
rm -f output/news_mast.json output/news_jmcode.json output/news_cont_p.json
rm -f output/bad/news_mast.bad.json output/bad/news_jmcode.bad.json output/bad/news_cont_p.bad.json

python repair_news_mast_json.py --input input/news_mast.json
python repair_news_jmcode_json.py --input input/news_jmcode.json
python repair_news_cont_p_json.py --input input/news_cont_p.json
```

정상이라면 실행 결과에서 `bad_rows=0`이 나와야 한다.

## 요약

기본 실행 명령은 다음 3개다.

```sh
python repair_news_mast_json.py --input input/news_mast.json
python repair_news_jmcode_json.py --input input/news_jmcode.json
python repair_news_cont_p_json.py --input input/news_cont_p.json
```

기본 출력은 다음 3개다.

```text
output/news_mast.json
output/news_jmcode.json
output/news_cont_p.json
```
