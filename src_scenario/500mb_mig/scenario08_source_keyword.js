import { equalsFilter, keywordPipeline, runScenario } from "./common.js";

await runScenario({
  scenario: "news_mig_500 시나리오 8",
  description: "뉴스구분과 검색어 조건으로 해당 뉴스매체의 뉴스를 검색합니다.",
  inputs: [
    { key: "dgubun", label: "뉴스구분", example: "P" },
    { key: "query", label: "검색어", example: "삼성전자 실적" },
  ],
  buildPipeline: ({ indexName, limit, dgubun, query }) =>
    keywordPipeline({
      indexName,
      limit,
      query,
      filters: [equalsFilter("dgubun", dgubun)],
    }),
});
