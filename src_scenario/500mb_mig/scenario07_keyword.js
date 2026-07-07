import { keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig_500 시나리오 7",
  description: "검색어만 사용해 전체 뉴스에서 검색합니다.",
  inputs: [{ key: "query", label: "검색어", example: "삼성전자 실적" }],
  buildPipeline: ({ indexName, limit, query }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
    }),
});
