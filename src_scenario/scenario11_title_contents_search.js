import { runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig_500 시나리오 11",
  description: "title 또는 contents에서 검색어를 조회합니다. 종목코드/뉴스구분 filter는 적용하지 않습니다.",
  inputs: [{ key: "query", label: "검색어", example: "삼성전자 실적" }],
  buildPipeline: ({ indexName, limit, query }) => [
    {
      $search: {
        index: indexName,
        text: {
          query,
          path: ["title", "contents"],
          matchCriteria: "all",
        },
        sort: {
          score: { $meta: "searchScore" },
          newscode_ts: -1,
        },
      },
    },
    { $limit: limit },
    {
      $project: {
        _id: 1,
        parent: 1,
        title: 1,
        contents: 1,
        dgubun: 1,
        shcode: 1,
        newscode_ts: 1,
        score: { $meta: "searchScore" },
      },
    },
  ],
});
