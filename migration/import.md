 ## import.sh 쉘 스크립트에 대한 설명
 

```bash

#!/bin/bash
# ↑ [쉬뱅(Shebang)] 이 파일이 Bash 쉘 스크립트임을 시스템에 알려주는 선언문입니다.

# ----------------------------------------------------
# [환경 변수 설정 영역]
# ----------------------------------------------------

# MongoDB 접속 주소(URI)를 변수에 저장합니다. (문법 오류였던 부분을 MONGODB_URI로 수정 완료)
MONGODB_URI="mongodb://dpocdb01,dpocdb02,dpocdb03/?w=1"

# ../input/ 폴더 안에 있는 모든 .data 파일 목록을 가져와 FILES 변수에 담습니다.
# ls -f 옵션은 파일 목록을 정렬하지 않고 빠르게 가져오기 위해 사용됩니다.
FILES=$(ls -f ../input/*.data)

# 현재 스크립트가 실행되고 있는 디렉토리의 전체 경로(Absolute Path)를 얻어 APATH 변수에 저장합니다.
APATH=$(pwd)

# 전처리(파일 수정)를 수행할 파이썬 스크립트의 상대 경로를 정의합니다.
EFIXER="../repair_news_cont_p_json.py"

# 전역 변수로 쓸 카운터(처리한 파일 수)와 마이그레이션 대상 컬렉션 리스트를 빈 값으로 초기화합니다.
count=0
MIGLIST=""


# ----------------------------------------------------
# [함수 정의 영역]
# ----------------------------------------------------

# 1. 오라클 줄바꿈 깨짐 현상을 교정해 주는 파이썬 스크립트를 실행하는 함수입니다.
function efixer {
    # 첫 번째 인자($1)로 넘어온 파일명을 IFILE 변수에 넣습니다. (예: 10_news_cont_h_1.data)
    IFILE=$1
    
    # 터미널에 어떤 파이썬 명령어를 실행할지 보여주기 위해 미리 문자열을 만듭니다.
    CMD="python3.9 ${EFIXER} --input ../input/${IFILE}"
    
    # 실행할 명령어를 화면에 출력합니다.
    echo $CMD
    
    # 실제로 파이썬 스크립트를 호출하여 데이터를 온전한 JSON으로 복원합니다.
    python3.9 ${EFIXER} --input ../input/${IFILE}
}

# 2. 복원된 JSON 파일을 몽고디비에 임포트하는 함수입니다.
function import2db {
    # 첫 번째 인자로 전달받은 변환된 파일명(.json)의 전체 경로를 만듭니다.
    FNAME=${APATH}/$1
    
    # 두 번째 인자로 전달받은 타겟 컬렉션명을 저장합니다.
    CNAME=$2
    
    # 세 번째 인자로 전달받은 현재 순서 번호(카운트)를 저장합니다.
    CURRENT_COUNT=$3

    # 변환된 JSON 파일의 행 수(라인 수)를 구합니다. (예: "1500 /data/10_news.json")
    NLINE=$(wc -l "$FNAME")

    # ${NLINE%% *}는 wc -l의 결과에서 파일명 부분은 버리고 순수 '숫자'만 남기는 Bash 문법입니다.
    # 화면에 "import["1"]: /data/news.json to news_coll: lines[1500]" 형식으로 진행률을 보여줍니다.
    echo "import[\"$CURRENT_COUNT\"]: $FNAME to $CNAME: lines[${NLINE%% *}]"

    # mongoimport 도구를 이용해 몽고디비에 JSON 데이터를 밀어 넣습니다.
    # 각 줄 끝의 역슬래시(\)는 명령어가 다음 줄로 이어진다는 뜻입니다.
    mongoimport \
        --uri "$MONGODB_URI" \
        --authenticationDatabase=admin \
        --authenticationMechanism=SCRAM-SHA-256 \
        -u admin -p admin \
        --db newsdb \
        --collection "$CNAME" \
        --drop \
        -j 4 \
        --type=json \
        --file "${FNAME}"
}

# 3. 전체 파일 리스트를 돌며 하나씩 작업을 지시하는 일괄 처리(Batch) 함수입니다.
function batch {
    # FILES 변수에 들어있는 파일 목록을 하나씩 순회합니다. (file 변수에 경로가 담김)
    for file in $FILES
    do
        # ${file##*/}는 경로명(예: ../input/abc.data)에서 앞의 디렉토리 경로를 떼고 파일명(abc.data)만 추출합니다.
        file="${file##*/}"
        
        # ${file%.*}는 파일명에서 맨 뒤의 확장자(.data)를 제거하여 순수 이름만 남깁니다. (예: abc)
        filenoext="${file%.*}"
        
        # 현재 처리하기 시작한 대상의 이름을 화면에 출력합니다.
        echo "Processing: $filenoext"
        
        # 만약 파일명이 "2_news_mast" 이거나 "3_news_jmcode" 라면 처리를 건너뜁니다.
        # (-o 옵션은 OR를 뜻하며, if 문의 대괄호 주변 공백은 문법상 반드시 필요합니다.)
        if [ "$filenoext" = "2_news_mast" -o "$filenoext" = "3_news_jmcode" ]; then
            echo "Skip... $file"
            continue  # 아래 코드를 실행하지 않고 다음 파일(루프)로 넘어갑니다.
        fi

        # 카운트 변수를 1 증가시킵니다.
        (( count++ ))
        
        # 파일명에서 마지막 밑줄(_)과 그 뒤의 문자를 지워 몽고디비 컬렉션명으로 삼습니다.
        # (예: "10_news_cont_h_1" -> "10_news_cont_h" 컬렉션이 됨)
        collname="${filenoext%*"_"}"
        
        # MIGLIST 변수가 아직 비어있다면 컬렉션명을 그냥 넣고,
        # 이미 데이터가 들어가 있다면 뒤에 쉼표(,)를 붙이고 이어서 붙입니다. (첫 칸에 쉼표가 들어가는 버그 수정)
        if [ -z "$MIGLIST" ]; then
            MIGLIST="$collname"
        else
            MIGLIST="${MIGLIST},$collname"
        fi

        # 예외 처리: 파일명이 "1_news_cont_p"인 경우는 임포트하지 않고 스킵합니다.
        if [ "$filenoext" = "1_news_cont_p" ]; then
            continue
        fi

        # 1. 줄바꿈이 깨진 원본 데이터 파일을 파이썬으로 가공하여 고쳐놓습니다.
        efixer "$file"

        # 2. 가공이 완료된 새 JSON 파일(예: abc.json)을 몽고디비에 임포트합니다.
        import2db "${filenoext}.json" "${collname}" "$count"
    done

    # 루프가 모두 완료된 후 처리 결과를 요약해 보여줍니다.
    echo "Import Complete: total[$count]"
    
    # 노드 배포 목록 등에 쓰일 최종 컬렉션 리스트 파일(node.miglist)을 생성합니다.
    echo "$MIGLIST" > node.miglist
}


# ----------------------------------------------------
# [실제 스크립트 실행 시작 지점]
# ----------------------------------------------------

# 정의해 둔 batch 함수를 호출하여 전체 마이그레이션 공정을 시작합니다.
batch

```
