import { equalsFilter, keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig 시나리오 4",
  description: "뉴스구분과 검색어 조건으로 title을 검색합니다.",
  inputs: [
    { key: "dgubun", label: "뉴스구분", example: "4" },
    { key: "query", label: "검색어", example: "삼성전자" },
  ],
  buildPipeline: ({ indexName, limit, dgubun, query }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
      filters: [equalsFilter("dgubun", dgubun)],
    }),
});
