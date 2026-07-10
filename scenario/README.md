# news_mig_500 Title-Only MQL 시나리오

`news_mig_500` 컬렉션과 `news5_search_index` 기준으로 생성되는 시나리오별 MQL을 정리한다.

## 기준

```text
Database: newsdb
Collection: news_mig_500
Search Index: news5_search_index
```

현재 Search Index는 아래 구조를 기준으로 한다.

```js
db.runCommand({
  createSearchIndexes: "news_mig_500",
  indexes: [
    {
      name: "news5_search_index",
      definition: {
        mappings: {
          dynamic: false,
          fields: {
            title: {
              type: "string",
              analyzer: "lucene.nori",
              searchAnalyzer: "lucene.nori"
            },
            contents: {
              type: "string",
              analyzer: "lucene.nori",
              searchAnalyzer: "lucene.nori"
            },
            shcode: {
              type: "document",
              fields: {
                shcode: {
                  type: "token"
                }
              }
            },
            dgubun: {
              type: "token"
            },
            newscode_ts: {
              type: "number"
            }
          }
        }
      }
    }
  ]
});
```

## 변경 기준

`news_mig_500`은 현재 `title/shcode` 문서와 `contents` 문서가 분리된 구조다.

따라서 1~8번 시나리오의 일반 검색은 `title`만 검색하도록 변경했다.

변경 전:

```js
text: {
  query: "삼성전자 실적",
  path: ["title", "contents"],
  matchCriteria: "all"
}
```

변경 후:

```js
text: {
  query: "삼성전자",
  path: "title",
  matchCriteria: "all"
}
```

1번 시나리오도 동일한 형태의 `compound.must` 구조로 맞췄다.

9번 fuzzy와 10번 highlight는 특수 기능 검증 시나리오이므로 기존 목적에 맞게 별도로 유지한다.

## 공통 실행 예시

아래 명령은 `kbpoc` 디렉토리에서 실행한다.

```sh
cd /Users/sumi.ryu/Documents/opencode/kbpoc
```

MQL만 확인하려면 `--dry-run`을 사용한다.

```sh
npm run mig500:4 -- --shcode 005930 --dgubun 4 --query "삼성전자" --limit 5 --dry-run
```

## 시나리오 1

조건:

```text
검색어 있음
종목코드 없음
뉴스구분 없음
title 검색 후 최신순 조회
```

실행:

```sh
npm run mig500:1 -- --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title"
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
      shcode: 1
    }
  }
]);
```

## 시나리오 2

조건:

```text
뉴스구분 있음
종목코드 없음
검색어 없음
뉴스구분 조건 조회
```

실행:

```sh
npm run mig500:2 -- --dgubun P --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "P"
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
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 3

조건:

```text
종목코드 있음
검색어 있음
뉴스구분 없음
종목코드 filter + title 검색
```

실행:

```sh
npm run mig500:3 -- --shcode 005930 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
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
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 4

조건:

```text
종목코드 있음
뉴스구분 있음
검색어 있음
종목코드 filter + 뉴스구분 filter + title 검색
```

실행:

```sh
npm run mig500:4 -- --shcode 005930 --dgubun 4 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          },
          {
            equals: {
              path: "dgubun",
              value: "4"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
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
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 5

조건:

```text
종목코드 있음
뉴스구분 없음
검색어 없음
종목코드 조건 조회
```

실행:

```sh
npm run mig500:5 -- --shcode 005930 --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
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
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 6

조건:

```text
종목코드 있음
뉴스구분 있음
검색어 없음
종목코드 + 뉴스구분 조건 조회
```

실행:

```sh
npm run mig500:6 -- --shcode 005930 --dgubun P --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        filter: [
          {
            equals: {
              path: "shcode.shcode",
              value: "005930"
            }
          },
          {
            equals: {
              path: "dgubun",
              value: "P"
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
      contents: 1,
      dgubun: 1,
      shcode: 1
    }
  }
]);
```

## 시나리오 7

조건:

```text
검색어 있음
종목코드 없음
뉴스구분 없음
title 전체 검색
```

실행:

```sh
npm run mig500:7 -- --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
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
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 8

조건:

```text
뉴스구분 있음
검색어 있음
종목코드 없음
뉴스구분 filter + title 검색
```

실행:

```sh
npm run mig500:8 -- --dgubun 4 --query "삼성전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자",
              path: "title",
              matchCriteria: "all"
            }
          }
        ],
        filter: [
          {
            equals: {
              path: "dgubun",
              value: "4"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
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
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" }
    }
  }
]);
```

## 시나리오 9

조건:

```text
Fuzzy 검색
title과 contents를 모두 should로 검색
```

9번은 fuzzy 기능 검증 목적이므로 `title`, `contents` should 검색을 유지한다.

실행:

```sh
npm run mig500:9 -- --query "삼영전자" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        should: [
          {
            text: {
              query: "삼영전자",
              path: "title",
              matchCriteria: "all",
              fuzzy: {
                maxEdits: 1,
                prefixLength: 1,
                maxExpansions: 50
              },
              score: {
                boost: {
                  value: 5
                }
              }
            }
          },
          {
            text: {
              query: "삼영전자",
              path: "contents",
              matchCriteria: "all",
              fuzzy: {
                maxEdits: 1,
                prefixLength: 1,
                maxExpansions: 50
              },
              score: {
                boost: {
                  value: 1
                }
              }
            }
          }
        ],
        minimumShouldMatch: 1
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      }
    }
  },
  {
    $addFields: {
      score: { $meta: "searchScore" }
    }
  },
  {
    $match: {
      score: { $gte: 1 }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: 1
    }
  }
]);
```

## 시나리오 10

조건:

```text
Highlight 검색
title과 contents highlight 확인
```

10번은 highlight 기능 검증 목적이므로 `title`, `contents` 검색과 highlight path를 유지한다.

실행:

```sh
npm run mig500:10 -- --query "삼성전자 실적" --limit 5
```

MQL:

```js
db.news_mig_500.aggregate([
  {
    $search: {
      index: "news5_search_index",
      compound: {
        must: [
          {
            text: {
              query: "삼성전자 실적",
              path: ["title", "contents"],
              matchCriteria: "all"
            }
          }
        ]
      },
      sort: {
        score: { $meta: "searchScore" },
        newscode_ts: -1
      },
      highlight: {
        path: ["title", "contents"]
      }
    }
  },
  { $limit: 5 },
  {
    $project: {
      _id: 1,
      newscode_ts: 1,
      title: 1,
      contents: 1,
      dgubun: 1,
      shcode: 1,
      score: { $meta: "searchScore" },
      highlights: { $meta: "searchHighlights" }
    }
  }
]);
```

## 참고

`news_mig_500`은 title/shcode 문서와 contents 문서가 분리된 구조다.

그래서 1~8번의 업무 검색은 parent document의 `title` 중심으로 수행한다.

본문까지 결과에 붙여야 하는 경우에는 title 검색 후 `parent` 기준 `$lookup`을 추가하는 별도 쿼리가 필요하다.
